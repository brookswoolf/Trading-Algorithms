# IMPORT LIBRARIES
#------------------
import numpy as np
import pandas as pd

# IMPORT PIPELINE
from quantopian.pipeline import Pipeline
from quantopian.pipeline import CustomFactor


# IMPORT TWO PIPELINE FUNCTIONS NECESSARY FOR ALGORITHM
from quantopian.algorithm import attach_pipeline, pipeline_output    

# IMPORT DATASETS  
from quantopian.pipeline.data.builtin import USEquityPricing  
from quantopian.pipeline.data import morningstar
from quantopian.pipeline.data import Fundamentals  

# IMPORT FILTERS, FACTORS, AND CLASSIFIERS  
from quantopian.pipeline.filters import QTradableStocksUS  
from quantopian.pipeline.factors import Returns

"""
This algorithm uses a double sort technique to rank and order stocks in the pipeline.
The positive/negative sign of cumulative monthly returns is used as a pre-filter
for the long/short baskets. Stocks are continuously ranked based on 21-day returns 
(average amount of trading days per month). Stocks in the long basket with the highest
21-day returns are bought long, and stocks in the short basket with the lowest 21-day
returns are sold short. The portfolio is set up to be dollar neutral and rebalances
once a month. 
"""
                
# INITIALIZE ALGORITHM                      
#-----------------------                   
def initialize(context):
    
    # UNIVERSE DECLARATION
    universe = QTradableStocksUS()
    
    # ATTACH PIPELINE NAME
    pipe = Pipeline(screen=universe)
    attach_pipeline(pipe, 'my pipe')
    
    # ADD SECTOR TO THE PIPELINE
    sector = Fundamentals.morningstar_sector_code.latest
    pipe.add(sector, 'sector')  
    
    # ADD MONTHLY RETURN FACTOR AND RANKED RETURN FACTOR
    monthly_return = Returns(window_length=21)
    monthly_rank = monthly_return.rank(mask=universe)
    pipe.add(monthly_return, 'Mreturn')
    pipe.add(monthly_rank, 'Mrank')
    
    # ADD CUMULATIVE MONTHLY RETURNS TO THE PIPELINE
    prod_return = np.prod(monthly_return)
    pipe.add(prod_return, 'prodReturn')
    
    # DEFINE OUR PRE-FILTERED LONG AND SHORT LISTS
    longs = (prod_return > 0) 
    pipe.add(longs, 'longs')    
    
        
# SETTINGS
#----------    
    
    # SCHEDULE SETTINGS FOR THE 'REBALANCE' FUNCTION
    schedule_function(func=rebalance, 
                      date_rule=date_rules.month_start(), 
                      time_rule=time_rules.market_open(), 
                      half_days=True)
    
    # SCHEDULE SETTINGS FOR THE 'RECORD VARS' FUNCTION
    schedule_function(func=record_vars,
                      date_rule=date_rules.month_start(),
                      time_rule=time_rules.market_open(),
                      half_days=True)

    
    # LEVERAGE SETTINGS (CAN BE ADJUSTED)
    context.long_leverage = 0.5
    context.short_leverage = -0.5 
    
    # SLIPPAGE SETTINGS (CAN BE ADJUSTED - DEFAULT)
    set_slippage(us_equities=slippage.FixedBasisPointsSlippage(basis_points=5, volume_limit=0.1)) 
            
    # COMMISSION SETTINGS (CAN BE ADJUSTED - SET TO INTERACTIVE BROKERS COMMISSION PRICING)
    set_commission(us_equities=commission.PerShare(cost=0.005, min_trade_cost=1))

       
# EVERYDAY BEFORE TRADING START: 
#--------------------------------                      
def before_trading_start(context, data):
    
    # CALL PIPELINE BEFORE TRADING START
    context.output = pipeline_output('my pipe')
    
    # IF A STOCK HAS ALREADY BEEN CATEGORIZED AS A LONG, TAKE THE TOP OF THE MONTHLY RETURNS
    for stock in context.output['longs'] == 0:     
        context.long_list = context.output.sort_values(['Mrank'], ascending=False).iloc[:50]
        
    # IF A STOCK HAS ALREADY BEEN CATEGORIZED AS NOT A LONG (SHORT), TAKE THE BOTTOM OF THE MONTHLY RETURNS
    for stock in context.output['longs'] != 0:
        context.short_list = context.output.sort_values(['Mrank'], ascending=False).iloc[-50:]  
                
                
# RECORD AND RETURN VARIABLES: RETURN THE TOP TEN RETURN RANKING STOCKS FROM THE LONG AND SHORT LISTS       
#-----------------------------------------------------------------------------------------------------           
def record_vars(context, data):  
    
    # RECORDED METRICS DURING BACKTEST -- LEVERAGE 
    record(leverage = context.account.leverage)
        
    # PRINT TOP 10 DAILY LONG AND SHORT POSITIONS
    print "Long List"
    log.info("\n" + str(context.long_list.sort_values(['Mrank'], ascending=True).head(10)))
    
    print "Short List" 
    log.info("\n" + str(context.short_list.sort_values(['Mrank'], ascending=True).head(10)))      
    
               
# REBALANCE
#-----------
def rebalance(context,data):
    
    # DEFINE THE TARGET WEIGHT OF EACH STOCK IN THE PORTFOLIO TO BE EQUAL ACROSS BOTH LISTS
    long_weight = context.long_leverage / float(len(context.long_list))
    short_weight = context.short_leverage / float(len(context.short_list))

    # FOR EACH STOCK THAT WE HAVE CLASSIFIED IN OUR LONG AND SHORT LISTS, 
    # WE WANT TO PLACE A MARKET ORDER BASED ON THE DEFINED TARGET PERCENT. 
    # THE ORDER WILL BE EXECUTED WHEN THE FUNCTION IS SCHEDULED TO BE CALLED 
    # (SEE SETTINGS)
     
    for long_stock in context.long_list.index:
        log.info("ordering longs")
        log.info("weight is %s" % (long_weight))
        order_target_percent(long_stock, long_weight)
       
        
    for short_stock in context.short_list.index:
        log.info("ordering shorts")
        log.info("weight is %s" % (short_weight))
        order_target_percent(short_stock, short_weight)
              
        
    # EXIT ANY POSITIONS THAT ARE NO LONGER ON OUR LONG OR SHORT LIST    
    for stock in context.portfolio.positions.iterkeys():
        if stock not in context.long_list.index and stock not in context.short_list.index:
            order_target(stock, 0)
