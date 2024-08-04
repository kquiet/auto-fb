#!/bin/bash

cd "$(dirname "$0")"

trap_handler() {
  echo 'Received signal, terminating application...'
  kill -TERM $APP_PID

  # Wait for the process to terminate gracefully with a timeout of 10 seconds
  for i in {1..10}; do
    if ps -p $APP_PID > /dev/null; then
      sleep 1
    else
      break
    fi
  done

  # If the process is still running after the timeout, force to terminate it and its child processes
  if ps -p $APP_PID > /dev/null; then
    echo "application did not terminate, forcefully killing it and its child processes..."
    kill -KILL $APP_PID
    pkill -P $APP_PID  # Kill any remaining child processes
  else
    echo "application terminated gracefully"
  fi

  wait $APP_PID
}

trap trap_handler SIGINT SIGTERM SIGQUIT

echo "starting appliation..."
./app &
APP_PID=$!
wait $APP_PID

echo "application exited."

read -n 1 -s -r -p "Press any key to exit..."