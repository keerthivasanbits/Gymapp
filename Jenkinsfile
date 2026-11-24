pipeline {
    agent any

    environment {
        PYTHONUNBUFFERED = '1'
        MPLBACKEND = 'Agg'
        DOCKER_IMAGE = '2026ht66046keer/gymapp'
        DOCKER_CREDENTIALS_ID = 'dockerhub-creds'
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
                    xvfb-run -a pytest aceestver_test_1.py --junitxml=test-results.xml -v
                '''
            }
        }

        stage('Build & Push Docker Image') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: env.DOCKER_CREDENTIALS_ID,
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh '''
                        docker build -t ${DOCKER_IMAGE}:${BUILD_NUMBER} -t ${DOCKER_IMAGE}:latest .
                        echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
                        docker push ${DOCKER_IMAGE}:${BUILD_NUMBER}
                        docker push ${DOCKER_IMAGE}:latest
                        docker logout
                    '''
                }
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