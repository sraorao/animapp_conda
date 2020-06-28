import pandas as pd

def fill_frames(dataframe):
    """
    Returns new dataframe without any missing frames.
    Fills the dataframe where frames are missing (e.g., when no object is detected in a frame). 
    "Filling" means adding a new row with the missing frame number with x and y coordinates exactly 
    the same as the preceding frame (so that the distance travelled is not affected)

    Keyword arguments:
    dataframe -- a pandas dataframe containing the labelled columns x, y, frame
    """

    filled_df = pd.DataFrame(columns = ['x', 'y', 'frame'])
    dataframe.index = pd.RangeIndex(len(dataframe.index))
    for i in range(1, dataframe.shape[0]):
        if (dataframe.frame[i] - dataframe.frame[i - 1]) > 1:
            for missing_frame in range(dataframe.frame[i-1] + 1, dataframe.frame[i]):
                filled_df.loc[missing_frame] = [dataframe.x[i-1], dataframe.y[i-1], missing_frame]
    dataframe = pd.concat([dataframe, filled_df])
    dataframe = dataframe.sort_values(by = 'frame', axis = 0)
    dataframe.index = pd.RangeIndex(len(dataframe.index))
    return(dataframe)

def calculate_velocity(dataframe):
    """
    returns the same dataframe object containing additional column 'velocity'

    Keyword arguments:
    dataframe -- a dataframe object containing columns x, y, frame (already filled using fill_frames())
    """

    from math import sqrt
    all_distances = []
    for i in range(0, dataframe.shape[0] - 1):
        all_distances.append(sqrt(((dataframe.x[i] - dataframe.x[i + 1])**2) + ((dataframe.y[i] - dataframe.y[i + 1])**2)))
    all_distances.insert(0, 0)
    dataframe['distance'] = pd.Series(all_distances, index = dataframe.index)
    return(dataframe)

def calculate_rolling_velocity(dataframe, n = 10):
    """
    Returns the same dataframe object containing additional column 'rolling_velocity'

    Keyword arguments:
    dataframe -- a datafrane object containing columns x, y, frame, velocity
    n -- integer number of frames over which to average over (rolling window)
    """

    total_frames = dataframe.shape[0]
    mean_distance_per_n_frames = [None] * total_frames
    def mean(list):
        return(sum(list)/len(list))
    for i in range(n, total_frames - (n + 1)):
        mean_distance_per_n_frames[i] = mean(dataframe.distance[i - n : i + n])
    dataframe['rolling_velocity'] = pd.Series(mean_distance_per_n_frames, index = dataframe.index)
    return(dataframe)

def filter_by_rolling_velocity(dataframe, cutoff):
    """
    Returns a new dataframe that satisfies the rolling velocity cutoff

    Keyword arguments:
    dataframe -- a pandas dataframe containing columns x, y, frame, velocity, rolling_velocity
    cutoff -- an integer to filter the given dataframe
    """

    return(dataframe[dataframe.rolling_velocity > cutoff])

