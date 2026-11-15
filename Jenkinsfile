// InterviewHub CI/CD pipeline
// Stages: checkout -> install -> lint -> security -> test+coverage -> sonar -> docker build -> deploy
pipeline {
    agent any

    environment {
        IMAGE = "interviewhub:${env.BUILD_NUMBER}"
        VENV  = ".venv"
    }

    options { timestamps(); timeout(time: 20, unit: 'MINUTES') }

    stages {
        stage('Checkout') {
            steps { checkout scm }
        }
        stage('Install') {
            steps {
                sh 'python3 -m venv $VENV && . $VENV/bin/activate && pip install -q -r requirements-dev.txt'
            }
        }
        stage('Lint') {
            steps { sh '. $VENV/bin/activate && flake8' }
        }
        stage('Security scan') {
            steps {
                sh '. $VENV/bin/activate && bandit -r app -ll -f txt -o bandit-report.txt || (cat bandit-report.txt && exit 1)'
                sh '. $VENV/bin/activate && pip-audit -r requirements.txt || true'
            }
        }
        stage('Unit tests + coverage') {
            steps {
                sh 'mkdir -p reports && . $VENV/bin/activate && pytest --junitxml=reports/junit.xml --cov-report=xml --cov-report=html'
            }
            post {
                always {
                    junit 'reports/junit.xml'
                    archiveArtifacts artifacts: 'htmlcov/**, coverage.xml, bandit-report.txt', allowEmptyArchive: true
                }
            }
        }
        stage('SonarQube analysis') {
            when { expression { return env.SONAR_HOST_URL != null } }
            steps {
                withSonarQubeEnv('SonarQube') { sh 'sonar-scanner' }
            }
        }
        stage('Docker build') {
            when { expression { return fileExists('Dockerfile') } }
            steps { sh 'docker build -t $IMAGE -t interviewhub:latest .' }
        }
        stage('Deploy (staging)') {
            when { allOf { branch 'main'; expression { return fileExists('Dockerfile') } } }
            steps {
                sh 'docker rm -f interviewhub-staging || true'
                sh 'docker run -d --name interviewhub-staging -p 8000:8000 -e JWT_SECRET=$JWT_SECRET interviewhub:latest'
                sh 'sleep 5 && curl -fsS http://localhost:8000/api/health'
            }
        }
    }
    post {
        success { echo 'Pipeline passed' }
        failure { echo 'Pipeline failed - check the stage logs above' }
    }
}
