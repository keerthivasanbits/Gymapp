pipeline {
    agent any

    environment {
        PYTHONUNBUFFERED = '1'
        MPLBACKEND = 'Agg'
    }

    stages {
        stage('Set Up Virtualenv & Dependencies') {
            steps {
                sh '''
                    rm -rf .venv
                    python3 -m venv .venv
                    . .venv/bin/activate
                    pip install --upgrade pip

                    # Install required Python dependencies
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
                    pytest aceestver_test_1.py --junitxml=test-results.xml -v
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