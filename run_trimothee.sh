# set preferred python version
# TRIMOTHEE_VENV should be defined

if [ -z "$TRIMOTHEE_VENV" ]; then
  echo "ERROR: TRIMOTHEE_VENV environment variable is not defined."
  echo "Please set TRIMOTHEE_VENV to your python venv directory before running this script."
  exit 1
fi

export APP_HOME=/home/pi/Trimothee/src
export CONFIG_PATH=$APP_HOME/config.json

# set preferred driver and client
export CLIENT_DIR=$APP_HOME/python_client
export DRIVER_DIR=$APP_HOME/drivers

export DRIVER_SESSION=trimothee_driver
export CLIENT_SESSION=trimothee_client

# kill existing tmux sessions
tmux kill-session -t $DRIVER_SESSION
tmux kill-session -t $CLIENT_SESSION

# run driver and client sessions
echo "Starting driver in TMUX - $DRIVER_SESSION"
tmux new -d -s $DRIVER_SESSION
tmux send-keys -t $DRIVER_SESSION "cd $DRIVER_DIR" Enter
tmux send-keys -t $DRIVER_SESSION "source ./run_driver.sh $CONFIG_PATH &" Enter

echo "Starting client in TMUX - $CLIENT_SESSION"
tmux new -d -s $CLIENT_SESSION
tmux send-keys -t $CLIENT_SESSION "cd $CLIENT_DIR" Enter
tmux send-keys -t $CLIENT_SESSION "source ./run_client.sh $CONFIG_PATH &" Enter
