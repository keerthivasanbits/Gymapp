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
                echo 'Installing Python dependencies'
                sh '''
                    python3 -m venv .venv
                    .venv/bin/pip install --upgrade pip
                    .venv/bin/pip install --no-cache-dir -r requirements.txt
                '''
            }
        }

        stage('Test') {
            steps {
                echo 'Running Automated Tests with xvfb-run'
                sh '''
                    # Activate venv
                    source .venv/bin/activate

                    # Install test dependencies
                    pip install pytest pytest-xvfb matplotlib

                    # Run tests inside virtual framebuffer
                    xvfb-run -a pytest aceestver_test_1.py --maxfail=1 --disable-warnings -q
                '''
            }
        }
    }
}
