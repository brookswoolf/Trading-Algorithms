# Multi-Factor Model Template

# I have developed the below algorithm using my own research, supplemented with the resources found in the Quantopian Lectures and Forums.
# This notebook was created and written by Brooks Woolfolk. All materials are for educational purposes. 

# Visit https://www.quantopian.com/algorithms/ if you would like to test and adjust the below. 
# You can implement any combination of the factors that you please ^_^


# IMPORT LIBRARIES
#------------------
# IMPORT PIPELINE
from quantopian.pipeline import Pipeline
from quantopian.pipeline import CustomFactor

# IMPORT TWO PIPELINE FUNCTIONS NECESSARY FOR ALGORITHM
from quantopian.algorithm import attach_pipeline, pipeline_output    

# IMPORT DATASETS  
from quantopian.pipeline.data.builtin import USEquityPricing  
from quantopian.pipeline.data import morningstar
from quantopian.pipeline.data.morningstar import valuation
from quantopian.pipeline.data import factset
from quantopian.pipeline.data import Fundamentals  

# IMPORT FILTERS, FACTORS, AND CLASSIFIERS  
from quantopian.pipeline.filters import QTradableStocksUS  
from quantopian.pipeline.factors import AverageDollarVolume,SimpleMovingAverage



# DEFINE CUSTOM FACTORS                      
#-----------------------                     

# FACTOR 1: ASSET TURNOVER
class AssetTurnover(CustomFactor):
    
    # predeclare your inputs and window length
    inputs = [Fundamentals.assets_turnover.latest]
    window_length=1
    
    # return out the assetturnover value 
    def compute(self, today, assets, out, assetturn):
        out[:] = assetturn

        
# FACTOR 2: RETURN ON EQUITY
class EquityReturn(CustomFactor):
    
    # predeclare your inputs and window length
    inputs = [Fundamentals.roe.latest]
    window_length=1
    
    # return out the roe value 
    def compute(self, today, assets, out, roe):
        out[:] = roe
    
 
# FACTOR 3: CAPEX USAGE = capex / sales
class CapexSales(CustomFactor):
    
    # predeclare your inputs and window length
    inputs = [Fundamentals.capital_expenditure.latest, Fundamentals.total_revenue.latest]
    window_length=1
    
    # return out the capex value 
    def compute(self, today, assets, out, capex, rev):
        out[:] = capex / rev
 

# FACTOR 4: DEBT FACTOR = total debt / enterprise value 
class DebtFactor(CustomFactor):
    
    # predeclare your inputs and window length
    inputs = [Fundamentals.total_debt.latest, Fundamentals.enterprise_value.latest]
    window_length=1
    
    # return out the debt / ev value 
    def compute(self, today, assets, out, debt, ev):
        out[:] = debt / ev
        

# FACTOR 5: PROFITABILITY FACTOR  
class ProfitFactor(CustomFactor):
    
    # predeclare your inputs and window length
    inputs = [Fundamentals.net_margin.latest]
    window_length=1
    
    # return out the net profit margin value 
    def compute(self, today, assets, out, margin):
        out[:] = margin

        
# FACTOR 6: SOLVENCY FACTOR 
class SolvencyFactor(CustomFactor):
    
    # predeclare your inputs and window length
    inputs = [Fundamentals.interest_coverage.latest]
    window_length=1
    
    # return out the interest coverage ratio value 
    def compute(self, today, assets, out, coverage):
        out[:] = coverage


# FACTOR 7: GROWTH FACTOR 
class GrowthFactor(CustomFactor):
    
    # predeclare your inputs and window length
    inputs = [Fundamentals.growth_score.latest]
    window_length=1
    
    # return out the morningstar growth score value 
    def compute(self, today, assets, out, growth):
        out[:] = growth

        
# FACTOR 8: VALUE FACTOR 
class ValueFactor(CustomFactor):
    
    # predeclare your inputs and window length
    inputs = [Fundamentals.value_score.latest]
    window_length=1
    
    # return out the morningstar value score value 
    def compute(self, today, assets, out, value):
        out[:] = value


# FACTOR 9: LIQUIDITY = Most recent trading volume / Shares outstanding
class Liquidity(CustomFactor):
    
    # predeclare your inputs and window length
    inputs = [USEquityPricing.volume, morningstar.valuation.shares_outstanding]
    window_length=1
    
    # return out the liquidity value  
    def compute(self, today, assets, out, volume, shares):
        out[:] = volume[-1]/shares[-1]
        
        
# FACTOR 10: MOMENTUM = Price of current day / Price of 60 days ago
class Momentum(CustomFactor):
    
    # predeclare your inputs and window length
    inputs = [USEquityPricing.close]
    window_length=60
    
    # return out the momentum value  
    def compute(self, today, assets, out, close):
        out[:] = close[-1]/close[0]
        
        
# FACTOR 11: MARKET CAP
class MarketCap(CustomFactor):
    
     # predeclare your inputs and window length
    inputs = [USEquityPricing.close, morningstar.valuation.shares_outstanding]
    window_length=1
    
    # return out the most recent market cap 
    def compute(self, today, assets, out, close, shares):
        out[:] = close[-1] * shares[-1]

        
                
# INITIALIZE ALGORITHM                      
#----------------------                     
def initialize(context):
    
    # ATTACH PIPELINE NAME
    pipe = Pipeline()
    attach_pipeline(pipe, 'quality pipe')
   
    # UNIVERSE DECLARATION (TOP 5000 STOCKS ACCORDING TO MARKET CAP)
    #mkt_cap = MarketCap()
    universe = QTradableStocksUS()#mkt_cap.top(5000)
    
    
    # ADD SECTOR TO THE PIPELINE
    sector = Fundamentals.morningstar_sector_code.latest
    pipe.add(sector, 'sector') 

    
    # ADD ASSET TURNOVER FACTOR AND RANK
    assetturn = AssetTurnover()
    #pipe.add(assetturn, 'assetturn')
    assetturn_rank = assetturn.rank(mask=universe)
    #pipe.add(assetturn_rank, 'assetturn_rank')    

    
    # ADD EQUITY RETURN FACTOR AND RANK
    roe = EquityReturn()
    #pipe.add(roe, 'roe')
    roe_rank = roe.rank(mask=universe)
    #pipe.add(roe_rank, 'roe_rank') 
    
    
    # ADD CAPEX FACTOR AND RANK
    capex = CapexSales()
    #pipe.add(capex, 'capex')
    capex_rank = capex.rank(mask=universe)
    #pipe.add(capex_rank, 'capex_rank') 
    
    
    # ADD DEBT FACTOR AND RANK
    debt = DebtFactor()
    #pipe.add(debt, 'debt')
    debt_rank = debt.rank(mask=universe)
    #pipe.add(debt_rank, 'debt_rank') 

  
    # ADD PROFIT FACTOR AND RANK
    profit = ProfitFactor()
    #pipe.add(profit, 'profit')
    profit_rank = profit.rank(mask=universe)
    #pipe.add(profit_rank, 'profit_rank') 
    
    
    # ADD SOLVENCY FACTOR AND RANK
    solv = SolvencyFactor()
    #pipe.add(solv, 'solv')
    solv_rank = solv.rank(mask=universe)
    #pipe.add(solv_rank, 'solv_rank') 
    
        
    # ADD GROWTH FACTOR AND RANK
    growth = GrowthFactor()
    #pipe.add(growth, 'growth')
    growth_rank = growth.rank(mask=universe)
    #pipe.add(growth_rank, 'growth_rank') 
    
    
    # ADD VALUE FACTOR AND RANK
    value = ValueFactor()
    #pipe.add(value, 'value')
    value_rank = value.rank(mask=universe)
    #pipe.add(value_rank, 'value_rank') 
   
    
    # ADD LIQUIDITY FACTOR AND RANK
    liquidity = Liquidity()
    #pipe.add(liquidity, 'liquidity')            
    liquidity_rank = liquidity.rank(mask=universe)
    #pipe.add(liquidity_rank, 'liquidity_rank')
    
    
    # ADD MOMENTUM FACTOR AND RANK
    momentum = Momentum()
    #pipe.add(momentum, 'momentum')                  
    momentum_rank = momentum.rank(mask=universe)
    #pipe.add(momentum_rank, 'momentum_rank')                
               
    
    # TAKE THE AVG OF THE RANKS FOR AN OVERALL QUALITY RANK
    quality_score = (assetturn_rank + roe_rank + capex_rank + debt_rank + profit_rank + solv_rank + growth_rank + value_rank + liquidity_rank + momentum_rank) / 10
    
    # YOU CAN TRY ANY VARIETY OF THE PREDEFINED FACTORS 
    # YOU CAN PLAY WITH THE ARITHMETIC, BUT BE CAREFUL OF OVERFITTING
    # quality_score =  (value_rank + liquidity_rank)
    
    pipe.add(quality_score.rank(mask=universe), 'quality_rank')
    pipe.add(quality_score, 'quality score')   
    

    
    
# SETTINGS
#----------   
        
    # PIPELINE SCREEN SETTINGS
    pipe.set_screen(universe & (momentum>0))
    
    # BENCHMARK SETTINGS (SPY DEFAULT)
    #set_benchmark(symbol('SPY'))
    
    # SCHEDULE SETTINGS FOR THE 'REBALANCE' FUNCTION
    schedule_function(func=rebalance, 
                      date_rule=date_rules.month_start(days_offset=0), 
                      time_rule=time_rules.market_open(hours=0,minutes=30), 
                      half_days=True)
    
    # SCHEDULE SETTINGS FOR THE 'RECORD VARS' FUNCTION
    schedule_function(func=record_vars,
                      date_rule=date_rules.every_day(),
                      time_rule=time_rules.market_close(),
                      half_days=True)

    
    # LEVERAGE SETTINGS (CAN BE ADJUSTED)
    context.long_leverage = 0.50
    context.short_leverage = -0.50 

    # SLIPPAGE SETTINGS (CAN BE ADJUSTED - DEFAULT)
    # set_slippage(us_equities=slippage.FixedBasisPointsSlippage(basis_points=5, volume_limit=0.1), 
    #              us_futures=slippage.FixedSlippage(spread=0))
            
    # COMMISSION SETTINGS (CAN BE ADJUSTED - DEFAULT)
    # set_commission(us_equities=commission.PerShare(cost=0.001, min_trade_cost=0), 
    #                us_futures=commission.PerContract(cost=1, exchange_fee=0.85, min_trade_cost=0))
                    
               
        
# EVERYDAY BEFORE TRADING START: 
#--------------------------------                 
def before_trading_start(context, data):
    
    # CALL PIPELINE BEFORE TRADING START (FILL N/A IS DEFAULT TO NaN)
    context.output = pipeline_output('quality pipe').fillna(1000)
      
    # DEFINE NUMBER OF SECURITIES TO LONG AND SHORT BASED ON INDEX LOCATION 
    context.long_list = context.output.sort_values(['quality_rank'], ascending=False).iloc[:100]
    context.short_list = context.output.sort_values(['quality_rank'], ascending=False).iloc[-100:]   

                
                
# RECORD AND RETURN VARIABLES: RETURN THE TOP TEN QUALITY RANKING STOCKS FROM THE LONG AND SHORT LISTS       
#------------------------------------------------------------------------------------------------------                          
def record_vars(context, data):  
    
    # RECORDED METRICS DURING BACKTEST -- LEVERAGE 
    record(leverage = context.account.leverage)
        
    # PRINT TOP 10 DAILY LONG AND SHORT POSITIONS
    print "Long List"
    log.info("\n" + str(context.long_list.sort_values(['quality_rank'], ascending=True).head(10)))
    
    print "Short List" 
    log.info("\n" + str(context.short_list.sort_values(['quality_rank'], ascending=True).head(10)))      
                
                
               
# REBALANCE
#-----------  
def rebalance(context,data):
    
    # DEFINE THE TARGET WEIGHT OF EACH STOCK IN THE PORTFOLIO
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
            
                 
