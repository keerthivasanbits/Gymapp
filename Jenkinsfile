pipeline {
    agent any
    triggers {
        githubPush()
    }

    stages {
        stage('Checkout') {
            steps {
                echo 'Checking out main branch'
                checkout scm
            }
        }

        stage('Build') {
            steps {
                echo 'Installing python dependencies'
                sh '''
                    python3 -m venv .venv
                    .venv/bin/pip install -r requirements.txt
                '''
            }
        }

        stage('Test') {
            steps {
                echo 'Running Automated Test with Virtual Display'
                sh '''
                    # Start virtual display on screen :99
                    Xvfb :99 -screen 0 1024x768x24 &
                    XVFB_PID=$!
                    
                    # Run tests against the virtual screen
                    DISPLAY=:99 .venv/bin/pytest aceestver_test_1.py
                    
                    # Terminate the background Xvfb process
                    kill $XVFB_PID || true
                '''
            }
        }
    }
}