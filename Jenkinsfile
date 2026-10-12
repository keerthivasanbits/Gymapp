pipeline {
    agent any

    environment {
        PYTHONUNBUFFERED = '1'
        MPLBACKEND = 'Agg'
        PATH = "/usr/local/bin:/usr/bin:/bin:/usr/local/sbin:/usr/sbin:/sbin:${env.PATH}"
    }

    stages {
        stage('Set Up Virtualenv & Dependencies') {
            steps {
                sh '''
                    rm -rf .venv
                    python3 -m venv .venv
                    . .venv/bin/activate
                    pip install --upgrade pip

                    # Core application dependencies
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

                    # Locate Xvfb if available in system paths
                    XVFB_BIN=$(command -v Xvfb || find /usr/bin /usr/local/bin /usr/X11R6/bin -name Xvfb 2>/dev/null | head -n 1)

                    if [ -n "$XVFB_BIN" ]; then
                        echo "Running tests with virtual framebuffer: $XVFB_BIN"
                        $XVFB_BIN :99 -screen 0 1024x768x24 -ac &
                        XVFB_PID=$!
                        sleep 1
                        DISPLAY=:99 pytest aceestver_test_1.py --junitxml=test-results.xml -v || TEST_EXIT=$?
                        kill $XVFB_PID || true
                    else
                        echo "Xvfb not detected in PATH, running tests headlessly"
                        pytest aceestver_test_1.py --junitxml=test-results.xml -v || TEST_EXIT=$?
                    fi

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
            echo 'Build failed. Check test-results.xml and Jenkins console log.'
        }
    }
}