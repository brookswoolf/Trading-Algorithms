# IMPORT MACHINE LEARNING LIBRARIES
from sklearn.ensemble import RandomForestRegressor
import numpy as np
import pandas as pd

# LEARNING OBJECTIVE: TRAIN MODEL TO LEARN AND PREDICT OUTPUT BASED ON RECENT PRICE MOVEMENTS
# METHOD: RANDOM FOREST REGRESSION
#----------------------------------

def initialize(context):    
    
    # TRADE APPLE STOCK
    context.security = sid(24)
    set_benchmark(symbol('AAPL'))
    
    # TRAINING PARAMETERS
    #---------------------
    
    # DEFINE TRAINING MODEL
    context.model = RandomForestRegressor()    
    
    # DEFINE LOOKBACK PERIOD ('N' DAYS TO LOOK BACK)
    context.lookback = 6
    
    # DEFINE HISTORY RANGE (HOW MANY DAYS SHOULD BE CONSIDERED IN MODEL)
    context.history_range = 300
    
    
    # SCHEDULE FUNCTIONS
    #--------------------    

    # TRADE EVERY DAY AT MARKET OPEN
    schedule_function(trade, date_rules.every_day(), time_rules.market_open())
    
    # CREATE A MODEL EVERY WEEK, 10 MINUTES BEFORE MARKET CLOSE
    schedule_function(create_model, date_rules.week_end(), time_rules.market_close(minutes=60))

    
# CREATE RANDOM REGRESSION MODEL    
#--------------------------------
def create_model(context, data):
    
    # GET DAILY PRICE VALUES FOR HISTORICAL DATE RANGE (USED TO CALCULATE DAILY CHANGES IN HISTORICAL PRICES)
    model_prices = data.history(context.security, 'price', context.history_range, '1d').values
    
    # CALCULATE DAILY CHANGES IN HISTORICAL PRICE
    price_changes = list(np.diff(model_prices))

    # LISTS TO STORE INPUT AND PREDICTION VARIABLES
    inputs = []; output = [] 
    
    # FOR EACH DATE IN HISTORICAL DATE RANGE
    for day in range(context.history_range-context.lookback-1):
        
        # FOR EACH DATE, STORE [CURRENT DAY PRICE CHANGE, DAY 2 PRICE CHANGE, ..., DAY 'N' PRICE CHANGE]
        inputs.append(price_changes[day:day+context.lookback]) 
        
        # FOR EACH DATE, STORE [DAY 'N' PRICE CHANGE]
        output.append(price_changes[day+context.lookback]) 
    
    # FIT OUR RANDOM FOREST MODEL
    context.model.fit(inputs, output) 

    
# TRADE LOGIC
#-------------    
def trade(context, data):
    
    if context.model: 
        
        # GET DAILY PRICE VALUES FOR LOOKBACK+1 DATE RANGE (USED TO CALCULATE DAILY CHANGES IN RECENT PRICES)
        recent_prices = data.history(context.security, 'price', context.lookback+1, '1d').values
        
        # CALCULATE DAILY CHANGES IN RECENT PRICES
        price_changes = list(np.diff(recent_prices))
       
        # USING RECENT CHANGES IN DAILY PRICES AS INPUT, PREDICT OUTPUT USING MODEL
        prediction = context.model.predict(price_changes)
        record(prediction = prediction)
        
        # TRADE LONG FOR POSITIVE PREDICTION, SHORT FOR NEGATIVE PREDICTION
        if prediction >= 1.0:
            order_target_percent(context.security, 2.0)
                
        elif (prediction < 1.0) and (prediction > -0.75):
            order_target_percent(context.security, 1.0)
            
        else:
            order_target_percent(context.security, -1.0)
