# Constrained Model
#-------------------

# I have developed the below algorithm using the resources found in the Quantopian Lectures and Forums. 
# This notebook was created and written by Brooks Woolfolk. All materials are for educational purposes. 

# Visit https://www.quantopian.com/algorithms/ if you would like to test and adjust the below ^_^


# IMPORT LIBRARIES
#------------------
import pandas as pd

import quantopian.algorithm as algo
import quantopian.optimize as opt

from quantopian.pipeline import Pipeline
from quantopian.pipeline.data import builtin, Fundamentals
from quantopian.pipeline.factors import AverageDollarVolume, RollingLinearRegressionOfReturns
from quantopian.pipeline.factors.fundamentals import MarketCap
from quantopian.pipeline.classifiers.fundamentals import Sector
from quantopian.pipeline.experimental import risk_loading_pipeline
from quantopian.pipeline.filters import QTradableStocksUS
from quantopian.pipeline.data import factset


# ALGORITHM PARAMETERS
#----------------------

def initialize(context):
    
    # DEFINE UNIVERSE
    # ------------------
    universe = QTradableStocksUS()

    
    # ALPHA GENERATION
    # ----------------
    # COMPUTE Z SCORES: ASSET TURNOVER AND CHANGE IN WORKING CAPITAL
    # BOTH ARE FUNDAMENTAL VALUE MEASURES
    
    asset_turnover = Fundamentals.assets_turnover.latest.winsorize(.05, .95).zscore()
    ciwc = Fundamentals.change_in_working_capital.latest.winsorize(.05, .95).zscore()
     
        
    # ALPHA COMBINATION
    # -----------------
    # ASSIGN EVERY ASSET AN ALPHA RANK AND CENTER VALUES AT 0 (DEMEAN).
    alpha = (asset_turnover + 2*ciwc).rank().demean()
    
    
    # BETA DEFINITION
    beta = 0.66*RollingLinearRegressionOfReturns(
                    target=sid(8554),
                    returns_length=5,
                    regression_length=252,
                    mask=alpha.notnull() & Sector().notnull()
                    ).beta + 0.33*1.0

    
    # CREATE AND REGISTER PIPELINE
    #-------------------------------
    # COMPUTES COMBINES ALPHA AND SECTOR CODE FOR UNIVERSE OF STOCKS TO BE USED IN OPTIMIZATION
    pipe = Pipeline(
        columns={
            'alpha': alpha,
            'sector': Sector(),
            'beta': beta,
        },
        # RETURN ONLY "NOT NULL" VALUES IN OUR PIPELINE
        screen=alpha.notnull() & Sector().notnull() & beta.notnull() & universe,
    )
    
    # LOAD ALL PIPELINES
    algo.attach_pipeline(pipe, 'pipe')
    algo.attach_pipeline(risk_loading_pipeline(), 'risk_loading_pipeline')
    
    
    # SCHEDULE FUNCTIONS
    #--------------------   
    algo.schedule_function(
        do_portfolio_construction,
        date_rule=algo.date_rules.week_start(),
        time_rule=algo.time_rules.market_open(minutes=10),
        half_days=False,
    )


# BEFORE TRADING START
#----------------------        
def before_trading_start(context, data):
    context.pipeline_data = algo.pipeline_output('pipe')
    context.risk_loading_pipeline = algo.pipeline_output('risk_loading_pipeline')


# PORTFOLIO CONSTRUCTION
#------------------------
def do_portfolio_construction(context, data):
    pipeline_data = context.pipeline_data

    # OBJECTIVE
    #-----------
    # OBJECTIVE: MAXIMIZE ALPHA BASED ON NAIVE RANKINGS 
    # RANK ALPHA COEFFICIENT AND TRADE TO MAXIMIZE THAT ALPHA
    # 
    # **NAIVE** OBJECTIVE MODEL 
    # WITH VERY SPREAD OUT ALPHA DATA, WE SHOULD EXPECT TO ALLOCATE
    # MAXIMUM AMOUNT OF CONSTRAINED CAPITAL TO HIGH/LOW RANKS
    #
    # A MORE SOPHISTICATED MODEL WOULD APPLY SOME SORT OF RE-SCALING
    objective = opt.MaximizeAlpha(pipeline_data.alpha)

    
    # CONTRAINT SETTINGS (CONTEST DEFAULT)
    # =========================================================================================
    
    # CONSTRAIN MAX GROSS LEVERAGE
    # IMPLICATIONS: ABSOLUTE VALUE OF OF LONG AND SHORT POSITIONS < OVERALL PORTFOLIO VALUE (1.0)
    MAX_GROSS_LEVERAGE = 1.0
    max_leverage = opt.MaxGrossExposure(MAX_GROSS_LEVERAGE)
    
    
    # CONSTRAIN MAX POSITION SIZE (LONG AND SHORT)
    # MAX POSITION <= 1% OF OVERALL PORTFOLIO
    MAX_SHORT_POSITION_SIZE = 0.01
    MAX_LONG_POSITION_SIZE = 0.01
    max_position_weight = opt.PositionConcentration.with_equal_bounds(-MAX_SHORT_POSITION_SIZE, 
                                                                      MAX_LONG_POSITION_SIZE)
                                                                            
    
    # CONSTRAIN CAPTIAL ALLOCATIONS FOR LONG AND SHORT EQUILLIBRIUM
    dollar_neutral = opt.DollarNeutral()
    
    
    # CONSTRAIN BETA-TO-SPY ***CONTEST CRITERIA***
    beta_neutral = opt.FactorExposure(pipeline_data[['beta']], 
                                      min_exposures={'beta': -0.05}, 
                                      max_exposures={'beta': 0.05})
        
    # CONSTRAIN COMMON SECTOR AND STYLE RISK FACTORS (NEWEST DEFAULT VALUES)
    # SECTOR DEFAULT: +-0.18
    # STYLE DEFAULT: +-0.36
    constrain_sector_style_risk = opt.experimental.RiskModelExposure(context.risk_loading_pipeline, 
                                                                     version=opt.Newest)
                                                                     
        
    # EXECUTE OPTIMIZATION
    # =========================================================================================
    # CALCULATE NEW WEIGHTS AND MANAGE MOVING PORTFOLIO TOWARD TARGET CAPITAL AND ASSET ALLOCATION
    algo.order_optimal_portfolio(objective=objective, 
                                 constraints=[max_leverage, 
                                              max_position_weight, 
                                              dollar_neutral, 
                                              constrain_sector_style_risk, 
                                              beta_neutral, 
                                              ])
