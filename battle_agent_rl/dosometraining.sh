#!/bin/sh
TEST_EPISODES=800
TRAIN_EPISODES=250
BEST_Q_TABLE="best_q_table.pkl"
total_trained=0
BEST_SCORE=""

rm -f "$BEST_Q_TABLE"

run_tests() {
  TEST_OUTPUT="$(./test_agent.sh "$TEST_EPISODES" 2>/dev/null)"
  printf '%s\n' "$TEST_OUTPUT"
  TEST_SCORE="$(
    printf '%s\n' "$TEST_OUTPUT" \
      | awk -F': *' '/^Score/{gsub(/^ +/, "", $2); print $2}'
  )"
}

update_best() {
  if [ -z "$TEST_SCORE" ]; then
    return
  fi

  is_better=$(awk -v current="$TEST_SCORE" -v best="$BEST_SCORE" '
    BEGIN {
      if (best == "") {
        print 1
      } else if (current > best) {
        print 1
      } else {
        print 0
      }
    }
  ')

  if [ "$is_better" -eq 1 ]; then
    BEST_SCORE="$TEST_SCORE"
    if [ -f "q_table.pkl" ]; then
      cp "q_table.pkl" "$BEST_Q_TABLE"
    fi
  fi
}

echo "Results after training on ${total_trained} episodes"
run_tests
update_best

i=1
while [ "$i" -le 10 ]; do
  ./train_qlearning.sh "$TRAIN_EPISODES" >/dev/null 2>&1
  total_trained=$(( total_trained + ${TRAIN_EPISODES:-0} ))
  echo "Results after training on ${total_trained} episodes"
  run_tests
  update_best
  i=$((i + 1))
done

if [ -n "$BEST_SCORE" ]; then
  echo "Highest score achieved: $BEST_SCORE"
else
  echo "Highest score achieved: N/A"
fi

