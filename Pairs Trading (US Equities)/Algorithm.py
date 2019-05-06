# THIS ALGORITHM PROVIDES A BASIC PAIRS TRADING STRATEGY ACROSS MULTIPLE PAIRS OF
# EQUITIES THAT ARE ASSUMED TO BE COINTEGRATED. THIS ALGORITHM IN ITS CURRENT STATE 
# SERVES AS A FRAMEWORK TO BACKTEST A PORTFOLIO OF MEAN REVERTING TRADING THEORIES

# *** THIS MODEL IS SIMPLY A FRAMEWORK AS NONE OF THE BELOW PAIRS HAVE CONFIRMED COINTEGRATION **
import numpy as np

def initialize(context):
    
    # INITIALIZE PAIRS
    #-----------------
    # AIRLINES
    context.aa = sid(45971)
    context.ual = sid(28051)
    # TECH
    context.goog = sid(26578)
    context.fb = sid(42950)
    # ENERGY ** need to change to ABGB/FSLR (per the quantopian pairs trade lecture)
    context.aee = sid(24783)
    context.exc = sid(22114)
    # CURRENCY **changed to canada and australia per Ernie Chan's backtested algo -- update the rest of the algo ***
    context.usa = sid(14516)
    context.eur = sid(14517) 
    
    # IDEALLY WE WOULD HAVE A MULTITUDE OF PAIRS THAT WE HAVE CONFIRMED 
    # ARE *CURRENTLY* COINTEGRATED PER OUR RESEARCH. ADDITIONAL PAIRS
    # ACTS AS A DIVERSIFICATION TOOL THAT PROTECTS THE PORTFOLIO FROM A 
    # PAIR DROPPING OUT OF COINTEGRATION --THUS NO ASSUMPTIONS CAN
    # CONTINUE TO BE MADE THAT THE SPREAD BETWEEN THE PAIR IS MEAN REVERTING.
    # DUE TO THIS FUNDAMENTAL PHENOMENON, WE MUST BE RIGOROUS IN TESTING NOT
    # ONLY NEW PAIRS, BUT ALSO OUR CURRENT ONES FOR CONTINUED COINTEGRATION.        
    
    # SCHEDULE FUNCTIONS
    schedule_function(check_pairs1, date_rules.every_day(), time_rules.market_open())
    schedule_function(check_pairs2, date_rules.every_day(), time_rules.market_open())
    schedule_function(check_pairs3, date_rules.every_day(), time_rules.market_open())
    schedule_function(check_pairs4, date_rules.month_start(), time_rules.market_open())
    
    # INITIALIZE THE FIRST LONG/SHORT POSITIONS TO FALSE SINCE WE HAVE NO TRADES YET
    context.long_on_spread1 = False
    context.shorting_spread1 = False
    
    # INITIALIZE THE SECOND LONG/SHORT POSITIONS TO FALSE SINCE WE HAVE NO TRADES YET
    context.long_on_spread2 = False
    context.shorting_spread2 = False
    
    # INITIALIZE THE THIRD LONG/SHORT POSITIONS TO FALSE SINCE WE HAVE NO TRADES YET
    context.long_on_spread3 = False
    context.shorting_spread3 = False
    
    # INITIALIZE THE FOURTH LONG/SHORT POSITIONS TO FALSE SINCE WE HAVE NO TRADES YET
    context.long_on_spread4 = False
    context.shorting_spread4 = False
    
# AIRLINE PAIR TRADE (AMERICAN/UNITED)
def check_pairs1(context,data):
    
# IN A FRAMEWORK WITH MULTIPLE PAIRS TRADING AT ONCE, WE WOULD ALLOCATE 
# LESS CAPITAL TO EACH PAIR AND SIMPLY COPY/PASTE THE CHECK_PAIRS TRADING FORMULA  
# RESPECTIVE TO EACH PAIR TRADING STRATEGY. KEEP IN MIND THAT CERTAIN VARIABLES MAY  
# NEED TO BE TWEAKED ACROSS DIFFERENT STRATEGIES --NAMELY THE LOOKBACK PERIOD, 
# TARGET PORTFOLIO WEIGHTS, AND POTENTIALLY THE Z SCORE THRESHOLDS (TRADE SIGNALS).

    aa = context.aa
    ual = context.ual
    
    # EACH TIME THE FUNCTION IS CALLED, RETURN THE 21 DAY PRICE HISTORY
    prices = data.history([aa,ual],'price',21,'1d')
    
    # RETURN MOST RECENT DAYS PRICES BASED ON ILOC[-1:]
    short_prices = prices.iloc[-1:] 
    
    # AVERAGE OF THE 21 DAY PRICE SPREAD  
    mavg_21 = np.mean(prices[aa] - prices[ual])
    # STDEV OF THE 21 DAY PRICE SPREAD
    std_21 = np.std(prices[aa] - prices[ual])
    
    # AVERAGE OF THE MOST RECENT DAYS PRICE SPREAD
    mavg_1 = np.mean(short_prices[aa] - short_prices[ual])
    
    # IF OUR STDEV IS GREATER THAN 0...
    if std_21 > 0:
        
        # CALCULATE THE Z SCORE BY DIVIDING (TODAYS AVERAGE SPREAD - THE 21 DAY AVERAGE SPREAD) 
        # BY THE 30 DAY STDEV
        zscore = (mavg_1 - mavg_21) / std_21
        
        # IF THE Z SCORE IS GREATER THAN ONE WE EXPECT THE MEAN TO REVERT, SO WE TRADE UNDER THAT ASSUMPTION
        if zscore > 1.0 and not context.shorting_spread1:
            order_target_percent(aa,0.5)
            order_target_percent(ual,-0.5)
            context.shorting_spread1 = True
            context.long_on_spread1 = False
            
        # IF THE Z SCORE IS LESS THAN ONE WE EXPECT THE MEAN TO REVERT, SO WE TRADE UNDER THAT ASSUMPTION    
        elif zscore < 1.0 and not context.long_on_spread1:
            order_target_percent(aa,-0.5)
            order_target_percent(ual,0.5)
            context.shorting_spread1 = False
            context.long_on_spread1 = True
        
        # IF THE Z SCORE IS LESS THAN 0.25 WE ASSUME THE MEAN HAS REVERTED (ENOUGH), SO WE EXIT OUT PAIRED POSITIONS
        elif abs(zscore) < 0.25:
            order_target_percent(aa,0)
            order_target_percent(ual,0)
            context.shorting_spread1 = False
            context.long_on_spread1 = False   

            
# TECH PAIR TRADE (GOOGLE/FACEBOOK)            
def check_pairs2(context,data):
    
# IN A FRAMEWORK WITH MULTIPLE PAIRS TRADING AT ONCE, WE WOULD ALLOCATE 
# LESS CAPITAL TO EACH PAIR AND SIMPLY COPY/PASTE THE CHECK_PAIRS TRADING FORMULA  
# RESPECTIVE TO EACH PAIR TRADING STRATEGY. KEEP IN MIND THAT CERTAIN VARIABLES MAY  
# NEED TO BE TWEAKED ACROSS DIFFERENT STRATEGIES --NAMELY THE LOOKBACK PERIOD, 
# TARGET PORTFOLIO WEIGHTS, AND POTENTIALLY THE Z SCORE THRESHOLDS (TRADE SIGNALS).

    goog = context.goog
    fb = context.fb
    
    # EACH TIME THE FUNCTION IS CALLED, RETURN THE 21 DAY PRICE HISTORY
    prices = data.history([goog,fb],'price',21,'1d')
    
    # RETURN MOST RECENT DAYS PRICES BASED ON ILOC[-1:]
    short_prices = prices.iloc[-1:] 
    
    # AVERAGE OF THE 21 DAY PRICE SPREAD  
    mavg_21 = np.mean(prices[goog] - prices[fb])
    # STDEV OF THE 21 DAY PRICE SPREAD
    std_21 = np.std(prices[goog] - prices[fb])
    
    # AVERAGE OF THE MOST RECENT DAYS PRICE SPREAD
    mavg_1 = np.mean(short_prices[goog] - short_prices[fb])
    
    # IF OUR STDEV IS GREATER THAN 0...
    if std_21 > 0:
        
        # CALCULATE THE Z SCORE BY DIVIDING (TODAYS AVERAGE SPREAD - THE 21 DAY AVERAGE SPREAD) 
        # BY THE 21 DAY STDEV
        zscore = (mavg_1 - mavg_21) / std_21
        
        # IF THE Z SCORE IS GREATER THAN ONE WE EXPECT THE MEAN TO REVERT, SO WE TRADE UNDER THAT ASSUMPTION
        if zscore > 1.0 and not context.shorting_spread2:
            order_target_percent(goog,0.5)
            order_target_percent(fb,-0.5)
            context.shorting_spread2 = True
            context.long_on_spread2 = False
            
        # IF THE Z SCORE IS LESS THAN ONE WE EXPECT THE MEAN TO REVERT, SO WE TRADE UNDER THAT ASSUMPTION    
        elif zscore < 1.0 and not context.long_on_spread2:
            order_target_percent(goog,-0.5)
            order_target_percent(fb,0.5)
            context.shorting_spread2 = False
            context.long_on_spread2 = True
        
        # IF THE Z SCORE IS LESS THAN 0.25 WE ASSUME THE MEAN HAS REVERTED (ENOUGH), SO WE EXIT OUT PAIRED POSITIONS
        elif abs(zscore) < 0.25:
            order_target_percent(goog,0)
            order_target_percent(fb,0)
            context.shorting_spread2 = False
            context.long_on_spread2 = False
            
            
# ENERGY PAIR TRADE (AMEREN/EXCELON)            
def check_pairs3(context,data):
    
# IN A FRAMEWORK WITH MULTIPLE PAIRS TRADING AT ONCE, WE WOULD ALLOCATE 
# LESS CAPITAL TO EACH PAIR AND SIMPLY COPY/PASTE THE CHECK_PAIRS TRADING FORMULA  
# RESPECTIVE TO EACH PAIR TRADING STRATEGY. KEEP IN MIND THAT CERTAIN VARIABLES MAY  
# NEED TO BE TWEAKED ACROSS DIFFERENT STRATEGIES --NAMELY THE LOOKBACK PERIOD, 
# TARGET PORTFOLIO WEIGHTS, AND POTENTIALLY THE Z SCORE THRESHOLDS (TRADE SIGNALS).

    aee = context.aee
    exc = context.exc
    
    # EACH TIME THE FUNCTION IS CALLED, RETURN THE 21 DAY PRICE HISTORY
    prices = data.history([aee,exc],'price',21,'1d')
    
    # RETURN MOST RECENT DAYS PRICES BASED ON ILOC[-1:]
    short_prices = prices.iloc[-1:] 
    
    # AVERAGE OF THE 21 DAY PRICE SPREAD  
    mavg_21 = np.mean(prices[aee] - prices[exc])
    # STDEV OF THE 21 DAY PRICE SPREAD
    std_21 = np.std(prices[aee] - prices[exc])
    
    # AVERAGE OF THE MOST RECENT DAYS PRICE SPREAD
    mavg_1 = np.mean(short_prices[aee] - short_prices[exc])
    
    # IF OUR STDEV IS GREATER THAN 0...
    if std_21 > 0:
        
        # CALCULATE THE Z SCORE BY DIVIDING (TODAYS AVERAGE SPREAD - THE 21 DAY AVERAGE SPREAD) 
        # BY THE 21 DAY STDEV
        zscore = (mavg_1 - mavg_21) / std_21
        
        # IF THE Z SCORE IS GREATER THAN ONE WE EXPECT THE MEAN TO REVERT, SO WE TRADE UNDER THAT ASSUMPTION
        if zscore > 1.0 and not context.shorting_spread3:
            order_target_percent(aee,0.5)
            order_target_percent(exc,-0.5)
            context.shorting_spread3 = True
            context.long_on_spread3 = False
            
        # IF THE Z SCORE IS LESS THAN ONE WE EXPECT THE MEAN TO REVERT, SO WE TRADE UNDER THAT ASSUMPTION    
        elif zscore < 1.0 and not context.long_on_spread3:
            order_target_percent(aee,-0.5)
            order_target_percent(exc,0.5)
            context.shorting_spread3 = False
            context.long_on_spread3 = True
        
        # IF THE Z SCORE IS LESS THAN 0.25 WE ASSUME THE MEAN HAS REVERTED (ENOUGH), SO WE EXIT OUT PAIRED POSITIONS
        elif abs(zscore) < 0.25:
            order_target_percent(aee,0)
            order_target_percent(exc,0)
            context.shorting_spread3 = False
            context.long_on_spread3 = False
            
            
            
# CURRENCY PAIR TRADE (USA/EUROPE)            
def check_pairs4(context,data):
    
# IN A FRAMEWORK WITH MULTIPLE PAIRS TRADING AT ONCE, WE WOULD ALLOCATE 
# LESS CAPITAL TO EACH PAIR AND SIMPLY COPY/PASTE THE CHECK_PAIRS TRADING FORMULA  
# RESPECTIVE TO EACH PAIR TRADING STRATEGY. KEEP IN MIND THAT CERTAIN VARIABLES MAY  
# NEED TO BE TWEAKED ACROSS DIFFERENT STRATEGIES --NAMELY THE LOOKBACK PERIOD, 
# TARGET PORTFOLIO WEIGHTS, AND POTENTIALLY THE Z SCORE THRESHOLDS (TRADE SIGNALS).

    usa = context.usa
    eur = context.eur
    
    # EACH TIME THE FUNCTION IS CALLED, RETURN THE 21 DAY PRICE HISTORY
    prices = data.history([usa,eur],'price',21,'1d')
    
    # RETURN MOST RECENT DAYS PRICES BASED ON ILOC[-1:]
    short_prices = prices.iloc[-1:] 
    
    # AVERAGE OF THE 21 DAY PRICE SPREAD  
    mavg_21 = np.mean(prices[usa] - prices[eur])
    # STDEV OF THE 21 DAY PRICE SPREAD
    std_21 = np.std(prices[usa] - prices[eur])
    
    # AVERAGE OF THE MOST RECENT DAYS PRICE SPREAD
    mavg_1 = np.mean(short_prices[usa] - short_prices[eur])
    
    # IF OUR STDEV IS GREATER THAN 0...
    if std_21 > 0:
        
        # CALCULATE THE Z SCORE BY DIVIDING (TODAYS AVERAGE SPREAD - THE 21 DAY AVERAGE SPREAD) 
        # BY THE 21 DAY STDEV
        zscore = (mavg_1 - mavg_21) / std_21
        
        # IF THE Z SCORE IS GREATER THAN ONE WE EXPECT THE MEAN TO REVERT, SO WE TRADE UNDER THAT ASSUMPTION
        if zscore > 1.0 and not context.shorting_spread4:
            order_target_percent(usa,0.5)
            order_target_percent(eur,-0.5)
            context.shorting_spread4 = True
            context.long_on_spread4 = False
            
        # IF THE Z SCORE IS LESS THAN ONE WE EXPECT THE MEAN TO REVERT, SO WE TRADE UNDER THAT ASSUMPTION    
        elif zscore < 1.0 and not context.long_on_spread4:
            order_target_percent(usa,-0.5)
            order_target_percent(eur,0.5)
            context.shorting_spread4 = False
            context.long_on_spread4 = True
        
        # IF THE Z SCORE IS LESS THAN 0.25 WE ASSUME THE MEAN HAS REVERTED (ENOUGH), SO WE EXIT OUT PAIRED POSITIONS
        elif abs(zscore) < 0.25:
            order_target_percent(usa,0)
            order_target_percent(eur,0)
            context.shorting_spread4 = False
            context.long_on_spread4 = False
