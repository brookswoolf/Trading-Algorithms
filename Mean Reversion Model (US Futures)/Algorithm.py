'''
I have edited this algorithm to make it much more readable and understandable with comments.
In deconstructing an algorithm, I find it interesting to see how all of the moving pieces are
working together in order to execute the trading strategy.

Author: Quantopian
Edits: Brooks Woolfolk

'''

import itertools
import scipy as sp
import numpy as np
import pandas as pd

import quantopian.optimize as opt
from statsmodels.tsa.stattools import coint
from quantopian.algorithm import order_optimal_portfolio

# Initialize funciton (ran at the beginning of the algo)
#-------------------------------------------------------
def initialize(context):

    
    # Define futures pairs in a list
    #--------------------------
    context.futures_pairs = [
        (continuous_future('LC', offset=0, roll='calendar', adjustment='mul'), 
         continuous_future('FC', offset=0, roll='calendar', adjustment='mul'))
        ,                   
        (continuous_future('CL', offset=0, roll='calendar', adjustment='mul'), 
         continuous_future('XB', offset=0, roll='calendar', adjustment='mul'))
        ,
        (continuous_future('SM', offset=0, roll='calendar', adjustment='mul'),
         continuous_future('BO', offset=0, roll='calendar', adjustment='mul'))
    ]
    
    # Deconstruct every group of pairs into one comprehensive list using itertools -- this list is 
    # called later in the rebalance function to store price data for each futures contract
    context.futures_list = list(itertools.chain.from_iterable(context.futures_pairs))
    
    # Initialize both the "inLong" dict and the "inShort" dict to False at the beginning
    # since we start with no positions in the portfolio -- this is updated as we order
    # and used to check True or False if we are already making a trade in one way to 
    # prevent the algorithm from trying to make a long or short bet on the same pair twice
    # at the same time
    context.inLong = {(pair[0].root_symbol, pair[1].root_symbol): False 
                      for pair in context.futures_pairs}    
    
    context.inShort = {(pair[0].root_symbol, pair[1].root_symbol): False 
                       for pair in context.futures_pairs}
    
    # Initialize weights for all futures to 0 in a dictionary
    context.long_term_weights = {cont_future.root_symbol: 0 for cont_future in context.futures_list}
    context.current_weights = {}
        
    # Strategic lookback periods that can be easily adjusted 
    # (2 months of trading days)
    context.long_ma = 42
    # (1 week of trading days)
    context.short_ma = 5
    
    # Schedule the rebalance_pairs function everyday, 60 minutes after the market open
    schedule_function(func=rebalance_pairs, 
                      date_rule=date_rules.every_day(), 
                      time_rule=time_rules.market_open(minutes=60))
   

# Order execution and rebalance function
#---------------------------------------
def rebalance_pairs(context, data):
    
    
    # Dataframe of historical prices (42 days per our definition) for every future that we are trading (futures_list)
    # Since we call the rebalance everyday, the prices in this dataframe will be rolling with time
    prices = data.history(context.futures_list, 'price', context.long_ma, '1d')
    
    # For each pair in futures_pairs, store the array of 42 day price history (prices) in Y,X variables respectively
    for future_y, future_x in context.futures_pairs:
        Y = prices[future_y]
        X = prices[future_x]
        
        # Take the log of the prices, these are used for an on the fly cointegration test below
        y_log = np.log(Y)
        x_log = np.log(X)
        
        # For each pair in futures_pairs, test for cointegration and return the status. If the pair 
        # goes through the cointegration test and has a pvalue greater than 0.05, they are definitely
        # no longer cointegrated and the "continue" statement skips this pair and reiterates the "for"
        # loop above -- for future_y, future_x in context.futures_pairs
        pvalue = coint(y_log, x_log)[1]
        if pvalue > 0.05:
            log.info('({} {}) are no longer cointegrated, no trades placed on this pair.'.format(future_y.root_symbol, 
                                                                                                  future_x.root_symbol))                                                                              
            continue
        
        # Since the pairs are deemd to be cointegrated, run a linear regression on the log of the
        # recent 42 day prices for X and Y
        regression = sp.stats.linregress(x_log[-context.long_ma:], 
                                         y_log[-context.long_ma:])
      
        # Since this is a continual algorithm meant to be run across multiple time periods,
        # retrieve and store the current contract that is being traded in the market
        future_y_contract, future_x_contract = data.current([future_y, future_x], 'contract')
        
        # Spread equals the price of Y - (X * slope of regression)
        # y = mx + b    ==>    y - mx = b    ==>   b = y - mx                                                            
        spreads = Y - (regression.slope * X)
        
        # Calculate the zscore of the spreads for mean reversion trading signals
        zscore = (np.mean(spreads[-context.short_ma:]) - np.mean(spreads)) / np.std(spreads, ddof=1)
        
        # Initialize the root_symbol of each contract in the pair into the current_weights dictionary       
        context.current_weights[future_y_contract] = context.long_term_weights[future_y_contract.root_symbol]
        context.current_weights[future_x_contract] = context.long_term_weights[future_x_contract.root_symbol]
        
        # Save the coefficient of the linear combination for later use
        hedge_ratio = regression.slope

        
# Trading Algorithms        
#-------------------------------------------------------------------------------------------------        
        # If the pair is in the short list AND the zscore of the spread is LESS THAN 0 (NEGATIVE):
        if context.inShort[(future_y.root_symbol, future_x.root_symbol)] and zscore < 0.0:
            
            # Set the weight for both contracts equal to 0 -- this is based on the economic theory that
            # if we are already shorting the spread, when the zscore is negative we want to exit all positions
            context.long_term_weights[future_y_contract.root_symbol] = 0
            context.long_term_weights[future_x_contract.root_symbol] = 0
            context.current_weights[future_y_contract] = context.long_term_weights[future_y_contract.root_symbol]
            context.current_weights[future_x_contract] = context.long_term_weights[future_x_contract.root_symbol]
            
            # Ensure the pair is no longer in either the long or short baskets
            context.inLong[(future_y.root_symbol, future_x.root_symbol)] = False
            context.inShort[(future_y.root_symbol, future_x.root_symbol)] = False
            continue
                                    
        #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # If the pair is in the long list AND the zscore of the spread is GREATER THAN 0 (POSTIVE):
        if context.inLong[(future_y.root_symbol, future_x.root_symbol)] and zscore > 0.0:
            
            # Set the weight for both contracts equal to 0 -- this is based on the economic theory that
            # if we are already long the spread, when the zscore is positive we want to exit all positions
            context.long_term_weights[future_y_contract.root_symbol] = 0
            context.long_term_weights[future_x_contract.root_symbol] = 0
            context.current_weights[future_y_contract] = context.long_term_weights[future_y_contract.root_symbol]
            context.current_weights[future_x_contract] = context.long_term_weights[future_x_contract.root_symbol]
            
            # Ensure the pair is no longer in either the long or short baskets
            context.inLong[(future_y.root_symbol, future_x.root_symbol)] = False
            context.inShort[(future_y.root_symbol, future_x.root_symbol)] = False
            continue
            
#------------------------------------------------------------------------------------------------- 
        # If the zscore of the spread is LESS THAN -1, AND pair is not already in the long basket:
        if zscore < -1.0 and (not context.inLong[(future_y.root_symbol, future_x.root_symbol)]):
            
            # Number of respective futures shares (used below in computeHoldingsPct)
            y_target_contracts = 1
            x_target_contracts = hedge_ratio
            
            # Put the pairs into the long list now that we are longing them
            context.inLong[(future_y.root_symbol, future_x.root_symbol)] = True
            context.inShort[(future_y.root_symbol, future_x.root_symbol)] = False
            
            # The target percentages are derived from the computeHoldingsPct function taking 
            # number of Y contracts, number of X contracts, (yPrice * yMultiplier), (xPrice * yMultiplier)
            (y_target_pct, x_target_pct) = computeHoldingsPct(y_target_contracts, 
                                                              x_target_contracts, 
                                                              future_y_contract.multiplier * Y[-1], 
                                                              future_x_contract.multiplier * X[-1])

            # Since we are now placing a long spread bet, we are going to buy Y at the target percent and
            # we are going to sell X at the target percent
            context.long_term_weights[future_y_contract.root_symbol] = y_target_pct
            context.long_term_weights[future_x_contract.root_symbol] = -x_target_pct
            context.current_weights[future_y_contract] = context.long_term_weights[future_y_contract.root_symbol]
            context.current_weights[future_x_contract] = context.long_term_weights[future_x_contract.root_symbol]
            continue
                        
        #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # If the zscore of the spread is GREATER THAN 1, AND pair is not already in the short basket:
        if zscore > 1.0 and (not context.inShort[(future_y.root_symbol, future_x.root_symbol)]):
            
            # Number of respective futures shares (used below in computeHoldingsPct)
            y_target_contracts = 1
            x_target_contracts = hedge_ratio
            
            # Put the pairs into the short list now that we are shorting them
            context.inLong[(future_y.root_symbol, future_x.root_symbol)] = False
            context.inShort[(future_y.root_symbol, future_x.root_symbol)] = True
            
            # The target percentages are derived from the computeHoldingsPct function taking 
            # number of Y contracts, number of X contracts, (yPrice * yMultiplier), (xPrice * yMultiplier)
            (y_target_pct, x_target_pct) = computeHoldingsPct(y_target_contracts, 
                                                              x_target_contracts, 
                                                              future_y_contract.multiplier * Y[-1], 
                                                              future_x_contract.multiplier * X[-1])
                
            # Since we are now placing a long spread bet, we are going to sell Y at the target percent and
            # we are going to buy X at the target percent. We store the target values in the long-term weights, 
            # and then transfer them to current_weights
            context.long_term_weights[future_y_contract.root_symbol] = -y_target_pct
            context.long_term_weights[future_x_contract.root_symbol] = x_target_pct
            context.current_weights[future_y_contract] = context.long_term_weights[future_y_contract.root_symbol]
            context.current_weights[future_x_contract] = context.long_term_weights[future_x_contract.root_symbol]
            continue
            
#------------------------------------------------------------------------------------------------- 
    
    # Calculate the adjusted weights and store them in a series that will be used for target weights in the portfolio.
    # We need to divide each weight stored in current_weights by the length of the pairs. In the calculations the
    # pairs are seen as individual units so each futures weight needs to be divided by the length of the pairs to 
    # get the ACTUAL weight in the overall portfolio
    adjusted_weights = pd.Series({i: w / (len(context.futures_pairs)) for i, w in context.current_weights.items()})
        
    # Using optimize api to order based on the adjusted_weights above, making sure to contrain net leverage to 1.0
    order_optimal_portfolio(opt.TargetWeights(adjusted_weights), constraints=[opt.MaxGrossExposure(1.0)])

    # Document the adjusted weights and leverage as we trade
    log.info('weights: ', adjusted_weights)
    record(Exposure = context.account.net_leverage)
    
#-------------------------------------------------------------------------------------------------    
# Function to compute the respective holdings percentages by taking the sum of the absolute value of 
# both dollar amounts (notionalDol) and dividing each of X and Y's dollar amounts by this, such that 
# the target percentages are a respective fraction of the total dollar sum of the pair. This is why 
# they are divided by the length of pairs in adjusted weights because in computeHoldingsPct they are 
# seen as a unit of 1. Therefore we need to divide each futures weight by the length of the pairs to 
# get the actual proportion (weight) of each future in the portfolio
def computeHoldingsPct(yShares, xShares, yPrice, xPrice):
    yDol = yShares * yPrice
    xDol = xShares * xPrice
    notionalDol =  abs(yDol) + abs(xDol)
    y_target_pct = yDol / notionalDol
    x_target_pct = xDol / notionalDol
    return (y_target_pct, x_target_pct)
