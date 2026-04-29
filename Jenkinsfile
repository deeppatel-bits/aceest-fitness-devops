pipeline {
    agent any

    environment {
        IMAGE_NAME = "ghcr.io/deeppatel-bits/aceest-fitness"
        REGISTRY   = "ghcr.io"
        GIT_REPO   = "https://github.com/deeppatel-bits/aceest-fitness-devops.git"
    }

    stages {

        stage('Checkout') {
            steps {
                echo '>>> Cloning repository...'
                git branch: 'main', url: "${GIT_REPO}"
            }
        }

        stage('Install Dependencies') {
            steps {
                echo '>>> Installing Python dependencies...'
                sh '''
                    pip install -r requirements.txt --quiet
                '''
            }
        }

        stage('Run Tests') {
            steps {
                echo '>>> Running Pytest unit tests...'
                sh '''
                    pytest tests/ -v --tb=short --junitxml=reports/test-results.xml
                '''
            }
            post {
                always {
                    junit 'reports/test-results.xml'
                }
            }
        }

        stage('Code Quality - SonarQube') {
            steps {
                echo '>>> Running SonarQube analysis...'
                withSonarQubeEnv('SonarQube') {
                    sh '''
                        sonar-scanner \
                          -Dsonar.projectKey=aceest-fitness \
                          -Dsonar.projectName="ACEest Fitness" \
                          -Dsonar.sources=app \
                          -Dsonar.tests=tests \
                          -Dsonar.python.coverage.reportPaths=reports/coverage.xml \
                          -Dsonar.language=py
                    '''
                }
            }
        }

        stage('Quality Gate') {
            steps {
                echo '>>> Checking SonarQube Quality Gate...'
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                echo '>>> Building Docker image...'
                sh """
                    docker build -t ${IMAGE_NAME}:${BUILD_NUMBER} .
                    docker tag ${IMAGE_NAME}:${BUILD_NUMBER} ${IMAGE_NAME}:latest
                """
            }
        }

        stage('Push to Registry') {
            steps {
                echo '>>> Pushing image to GitHub Container Registry...'
                withCredentials([string(credentialsId: 'GITHUB_PAT', variable: 'PAT')]) {
                    sh """
                        echo \$PAT | docker login ghcr.io -u deeppatel-bits --password-stdin
                        docker push ${IMAGE_NAME}:${BUILD_NUMBER}
                        docker push ${IMAGE_NAME}:latest
                    """
                }
            }
        }

        stage('Deploy - Rolling Update') {
            steps {
                echo '>>> Deploying with Rolling Update strategy...'
                sh """
                    kubectl apply -f k8s/deployment.yaml
                    kubectl set image deployment/aceest-fitness \
                        aceest-fitness=${IMAGE_NAME}:${BUILD_NUMBER} \
                        --record
                    kubectl rollout status deployment/aceest-fitness --timeout=120s
                """
            }
        }
    }

    post {
        success {
            echo '>>> Pipeline completed successfully!'
        }
        failure {
            echo '>>> Pipeline failed! Check logs above.'
        }
        always {
            sh 'docker rmi ${IMAGE_NAME}:${BUILD_NUMBER} || true'
        }
    }
}