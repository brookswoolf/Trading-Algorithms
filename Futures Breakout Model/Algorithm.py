"""
Futures Breakout Trading Model 
Author: Brooks Woolfolk


The Turtle Trading Strategy was a Complete Trading System taught by well-known traders Richard Dennis 
and Bill Eckhardt in an experiment where they tried to determine if trading skills can be taught to anyone. 
The Turtle group returned ~80% per year on average over the course of four years. This algorithm was written  
in an attempt to capture the same markets and trade signals. 

Channel Breakout System
Entry Signals:

    System 1 Entry: (20)
    If the price exceeded the rolling 20-day high by one tick, buy 1 Unit in market(long)
    If the price dropped below the rolling 20-day low by one tick, sell 1 Unit in market (short)

    System 2 Entry: (55)
    If the price exceeded the rolling 55-day high by one tick, buy 1 Unit in market(long)
    If the price dropped below the rolling 55-day low by one tick, sell 1 Unit in market (short)
    
Exit Signals:

    System 1 Exit: (10)
    If the price dropped below the rolling 10-day low by one tick, exit long position
    If the price exceeded the rolling 10-day high by one tick, exit short position

    System 2 Exit: (20)
    If the price dropped below the rolling 20-day low by one tick, exit long position
    If the price exceeded the rolling 20-day high by one tick, exit short position
 
 
    In this model, we are going to be trading System 1. 


The full risk management model is a risk constraint I would like to implement down the road:

Risk Management in Units
------------------------     Max Units
1 Single Market:                4
2 Closely Correlated Market:    6
3 Loosely Correlated Market:    10
4 Single Direction- Long/Short: 12

The back tester uses Interactive Brokers Commission table and proprietary slippage model
based on a rebuilt order book and volume metrics for accurate transaction cost effect  

"""

import math
import numpy as np
from talib import ATR


def initialize(context):
    
    
    # Define all of the Turtle's tradable futures that work in the backtesting IDE.
    # Since the Turtles did not trade every futures market, the fact they don't all
    # work seems to be a natural and convenient way to narrow down our markets.
    
    context.sugar = continuous_future('SB', offset=0, roll='volume', adjustment='mul')
    context.crude_oil = continuous_future('CL', offset=0, roll='volume', adjustment='mul')
    context.heating_oil = continuous_future('HO', offset=0, roll='volume', adjustment='mul')
    context.gold = continuous_future('GC', offset=0, roll='volume', adjustment='mul')
    context.silver = continuous_future('SV', offset=0, roll='volume', adjustment='mul')
    context.copper = continuous_future('HG', offset=0, roll='volume', adjustment='mul')
    context.sp500 = continuous_future('SP', offset=0, roll='volume', adjustment='mul')
    context.sp500_emini = continuous_future('ES', offset=0, roll='volume', adjustment='mul')
    context.wheat = continuous_future('WC', offset=0, roll='volume', adjustment='mul')
    context.wheat_emini = continuous_future('MW', offset=0, roll='volume', adjustment='mul')
    
    # Create a list of our futures
    context.my_futures = [context.sugar, 
                          context.crude_oil, 
                          context.heating_oil, 
                          context.gold, 
                          context.silver, 
                          context.copper,  
                          context.sp500, 
                          context.sp500_emini, 
                          context.wheat,
                          context.wheat_emini,
                          ]  
    
    
    # (Equity market it open for 6 hours and 30 minutes) 8:30am - 3:00pm
    # This is also the time of day where the futures market is the MOST liquid
    # total_minutes is just the total number of minutes the market is open
    
    #total_minutes = 6 * 60 + 30

    #Check for trades every five minutes
    
    # for i in range(1, total_minutes):        
        
    #     if i % 10 == 0:
    #         schedule_function(rebalance, 
    #                           date_rules.every_day(), 
    #                           time_rules.market_open(minutes=i), 
    #                           True)
    
        
    schedule_function(rebalance, date_rules.every_day(), time_rules.market_open())
    
    # Record the number of long and short positions at market close every day 
    schedule_function(record_vars, date_rules.every_day(), time_rules.market_close())
    

def rebalance(context, data):
        
    # Return the 20-day 'high', 'low', and 'close' for True Range calculation
    price_history = data.history(context.my_futures, ['high', 'low', 'close', 'price'], 21, '1d') 
    
    # Return the 10-day 'price' history of our futures
    recent_prices = data.history(context.my_futures, ['high', 'low', 'price'], 10, '1d') 
    
    # Return the current contract of each of our futures
    contracts = data.current(context.my_futures, 'contract')
    

    # TRADE LOGIC
    #-------------
    for future in context.my_futures:
        
        # Position size constraints
        starting_cash = context.portfolio.starting_cash
        position_size = starting_cash * 0.01        
   
        future_contract = contracts[future]          
               
        # N CALCULATION (VOLATILITY METRIC)
        #---------------------------------
        highs = price_history['high'][future]
        lows = price_history['low'][future]
        closes = price_history['close'][future]

        # N is the 20-Day Average True Range    
        N = ATR(highs, lows, closes, timeperiod=20)[-1]     
    
        if np.isnan(N):
            continue
            
            
        # DOLLAR VOLATILITY ADJUSTMENT
        #------------------------------
        # Dollar Volatility
        dV = N * future_contract.multiplier
                
        # Unit Calculation 
        unit = math.floor(position_size / dV)
 
        price = data.current(future, 'price')

        
        # Logs to see the price and unit data every time the function is called
        # log.info("Today's price of %s is: " % (future_contract.asset_name) + str(price))
        # log.info("The 20-day high of %s is: " % (future_contract.asset_name) + str(max(price_history['high'][future]))
        # log.info("The 20-day low of %s is: " % (future_contract.asset_name) + str(min(price_history['low'][future]))
        # log.info("Current unit of %s is: " % (future_contract.asset_name) + str(unit))
    
        high_20 = True if price >= max(price_history['high'][future]) else False
        low_20 = True if price <= min(price_history['low'][future]) else False
        
        high_10 = True if price >= max(recent_prices['high'][future]) else False
        low_10 = True if price <= min(recent_prices['low'][future]) else False

        
        # ENTRY STRATEGY
        #----------------
        # Long Entry
        if high_20:
            log.info("Entering long position in %s at $" % (future_contract.asset_name) + str(price))
            order(future_contract, unit)
            
        # Short Entry    
        elif low_20:
            log.info("Entering short position in %s at $" % (future_contract.asset_name) + str(price))
            order(future_contract, -unit)
        
        
        # EXIT STRATEGY 
        #---------------
        # Long Exit
        elif low_10:
            log.info("Exiting long position in %s at $" % (future_contract.asset_name) + str(price))
            order_target_percent(future_contract, 0)  

        # Short Exit
        elif high_10:
            log.info("Exiting short position in %s at $" % (future_contract.asset_name) + str(price))
            order_target_percent(future_contract, 0)            
        
        else:
            pass
      
        
        # CHECK POSITIONS
        #-----------------
        current_position = context.portfolio.positions[data.current(context.my_futures, 'contract')[future]]
        current_contract = current_position.asset        

        if current_contract in context.portfolio.positions and data.can_trade(current_contract) and not get_open_orders(current_contract):
            
            # Positon details
            cost_basis = context.portfolio.positions[current_contract].cost_basis             
            price = data.current(current_contract, 'price')
            holding = context.portfolio.positions[current_contract].amount
            
            long_position = True if holding > 0 else False
            short_position = True if holding < 0 else False         
   
            # Log details for each position
            log.info("=================================")
            log.info("Position details for %s" % str(current_contract.asset_name))
            log.info("The price is $ %s" % str(price))
            log.info("We are holding %s shares" % str(holding))
            log.info("Our cost basis is $ %s" % str(cost_basis))
            log.info("Dollar value is $ %s" % str(abs((cost_basis * holding) * current_contract.multiplier)))
            log.info("=================================")
                             
                
            # ADDING UNITS (Units are added at N/2 intervals)
            #---------------------------------------------------   
            # Additional Long Unit     
            if price >= (cost_basis + (N / 2)) and long_position:
                log.info("Purchased additional unit of %s at $" % (future_contract.asset_name) + str(price))
                log.info("N is %s" % str(N))
                order (current_contract, unit)

            # Additional Short Unit
            if price <= (cost_basis - (N / 2)) and short_position:
                log.info("Shorted additional unit of %s at $" % (future_contract.asset_name) + str(price))
                log.info("N is %s" % str(N))
                order(current_contract, -unit)  


            # STOP LOSSES (We stop out at +/-1.05 * our cost_basis)
            #-------------------------------------------
            # Long Loss
            if price <= (cost_basis * -1.05) and long_position:
                log.info("Stopped out of long in %s at $" % (future_contract.asset_name) + str(price))
                order_target_percent(current_contract, 0)  

            # Short Loss
            if price >= (cost_basis * 1.05) and short_position:
                log.info("Stopped out of short in %s at $" % (future_contract.asset_name) + str(price))
                order_target_percent(current_contract, 0)  

                                          
     
# RECORD VARIABLES
#------------------
def record_vars(context, data):
    
    portfolio_value = context.portfolio.portfolio_value
    #holdings = context.portfolio.positions
    
    # Log portfolio information (current value and positions)
    log.info("Current portfolio value : $" + str(portfolio_value))
    #log.info("Current holdings are :$" + str(holdings))

