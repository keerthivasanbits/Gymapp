pipeline {
    agent any

    environment {
        DISPLAY = ':99'
        PYTHONUNBUFFERED = '1'
    }

    stages {
        stage('Set Up Virtualenv & Dependencies') {
            steps {
                sh '''
                    rm -rf .venv
                    python3 -m venv .venv
                    . .venv/bin/activate
                    pip install --upgrade pip

                    # Project dependencies
                    pip install matplotlib fpdf2 pytest pytest-cov

                    if [ -f requirements.txt ]; then
                        pip install -r requirements.txt
                    fi
                '''
            }
        }

        stage('Execute Pytest') {
            steps {
                sh '''
                    . .venv/bin/activate

                    # Start virtual display if not already running on :99
                    Xvfb :99 -screen 0 1024x768x24 &
                    XVFB_PID=$!

                    # Run tests
                    pytest aceestver_test_1.py \
                        --junitxml=test-results.xml \
                        -v || TEST_EXIT=$?

                    # Terminate virtual display process
                    kill $XVFB_PID || true

                    # Exit with pytest status code
                    exit ${TEST_EXIT:-0}
                '''
            }
        }
    }

    post {
        always {
            junit allowEmptyResults: true, testResults: 'test-results.xml'
        }
        cleanup {
            sh 'rm -rf .venv test_fitness.db aceest_fitness.db'
        }
        failure {
            echo 'Build or tests failed. Inspect console output and test-results.xml.'
        }
    }
}