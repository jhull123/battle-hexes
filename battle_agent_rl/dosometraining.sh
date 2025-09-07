#!/bin/sh
TEST_EPISODES=800
TRAIN_EPISODES=250
total_trained=0

echo "Results after training on ${total_trained} episodes"
./test_agent.sh "$TEST_EPISODES" 2> /dev/null

i=1
while [ "$i" -le 10 ]; do
  ./train_qlearning.sh "$TRAIN_EPISODES" >/dev/null 2>&1
  total_trained=$(( total_trained + ${TRAIN_EPISODES:-0} ))
  echo "Results after training on ${total_trained} episodes"
  ./test_agent.sh "$TEST_EPISODES" 2>/dev/null
  i=$((i + 1))
done

