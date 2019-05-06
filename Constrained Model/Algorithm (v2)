# IMPORT LIBRARIES
#-----------------
from quantopian.algorithm import attach_pipeline, pipeline_output, order_optimal_portfolio
from quantopian.optimize import MaximizeAlpha, MaxGrossExposure, PositionConcentration, DollarNeutral, experimental, FactorExposure, Newest

from quantopian.pipeline import Pipeline, CustomFactor
from quantopian.pipeline.filters import QTradableStocksUS 
from quantopian.pipeline.classifiers.fundamentals import Sector
from quantopian.pipeline.experimental import risk_loading_pipeline
from quantopian.pipeline.data import builtin, Fundamentals, factset
from quantopian.pipeline.data.builtin import USEquityPricing
from quantopian.pipeline.factors import AverageDollarVolume, RollingLinearRegressionOfReturns, MarketCap

# CUSTOM MOMENTUM FACTOR
#-----------------------
class Momentum(CustomFactor):
    # predeclare your inputs and window length
    inputs = [USEquityPricing.close]
    window_length=3
    
    # return out the momentum value  
    def compute(self, today, assets, out, close):
        out[:] = close[0]/close[-1]
        
# ALGORITHM PARAMETERS
#---------------------        
def initialize(context):

    universe = QTradableStocksUS()
    sector = Sector()
    momentum = Momentum()
    pipe = Pipeline()
    pipe.add(sector, 'sector')
    
    # ALPHA
    asset_turnover = Fundamentals.assets_turnover.latest.winsorize(.05, .95).zscore()
    ciwc = Fundamentals.change_in_working_capital.latest.winsorize(.05, .95).zscore()

    alpha = (asset_turnover + ciwc).rank().demean()
    pipe.add(alpha, 'alpha')
    
    # BETA
    beta = RollingLinearRegressionOfReturns(target=sid(8554),
                                            returns_length=5,
                                            regression_length=252,
                                            mask=alpha.notnull() & Sector().notnull()
                                            ).beta                    
    pipe.add(beta, 'beta')
    
    # REGISTER PIPELINES
    # ------------------
    attach_pipeline(pipe, 'pipe')
    attach_pipeline(risk_loading_pipeline(), 'risk_loading_pipeline')
    pipe.set_screen(alpha.notnull() & Sector().notnull() & beta.notnull() & universe & (momentum>0))
    
    # SCHEDULE FUNCTIONS
    # ------------------   
    schedule_function(rebalance, 
                      date_rule=date_rules.every_day(), 
                      time_rule=time_rules.market_open(minutes=10))

    
# BEFORE TRADING START
# --------------------        
def before_trading_start(context, data):
    context.output = pipeline_output('pipe')
    context.risk_loading_pipeline = pipeline_output('risk_loading_pipeline')
    record(leverage = context.account.leverage)

    
# REBALANCE (OPTIMIZED PORTFOLIO ORDER EXECUTION)
# -----------------------------------------------
def rebalance(context, data):
     
    # OBJECTIVES
    objective = MaximizeAlpha(context.output.alpha)
    leverage = 1.05
    max_short = -0.025
    max_long = 0.025
   
    # CONSTRAINTS
    max_leverage = MaxGrossExposure(leverage)
    max_position_weight = PositionConcentration.with_equal_bounds(max_short, max_long)
    dollar_neutral = DollarNeutral(tolerance=0.005)
    constrain_sector_style_risk = experimental.RiskModelExposure(context.risk_loading_pipeline, version=Newest)                                                                     
    beta_neutral = FactorExposure(context.output[['beta']], min_exposures={'beta': -0.1}, max_exposures={'beta': 0.1})
                                      
    # ORDER OPTIMIZED PORTFOLIO
    order_optimal_portfolio(objective=objective, constraints=[max_leverage, 
                                                              max_position_weight, 
                                                              dollar_neutral, 
                                                              constrain_sector_style_risk, 
                                                              beta_neutral, 
                                                              ])
