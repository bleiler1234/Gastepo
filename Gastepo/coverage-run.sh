#!/usr/bin/env bash
# Description: Code Coverage Analysis With SonarQube
# Developer: yuzhonghua
# Date: 2020-09-25 11:20

echo "[Initial]: Now erase code coverage history..."
coverage erase
echo "[Success]: code coverage history has been erased successfully!"
echo "[Collect]: Now begin collect code coverage..."
coverage run --branch -a --include=TestSuite/TestMain/**/*Runner.py Run.py
echo "[Success]: code coverage has been collected successfully!"
echo "[Report]: Now display simple code coverage report..."
coverage report -i --include=TestSuite/TestMain/**/*Runner.py
echo "[Success]: Please review simple code coverage report above."
echo "[Generate]: Now generate code coverage xml report file..."
coverage xml -i -o Output/Coverage/coverage.xml
echo "[Success]: code coverage xml report file has been generated successfully!"
echo "[Analysis]: Now begin sonar-scanner analysis..."
#sonar-scanner
echo "[Done]: sonar-scanner analysis done, Please review related information on SonarQube web platform!"