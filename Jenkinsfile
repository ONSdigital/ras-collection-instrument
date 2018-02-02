pipeline {
    agent any

    triggers {
        pollSCM('* * * * *')
    }

    stages {
        stage('build') {
            agent {
                docker {
                    image 'kennethreitz/pipenv:latest'
                }

            }
            steps {
                git(url: 'https://github.com/ONSdigital/ras-collection-instrument.git')
                sh 'pipenv install --dev --deploy'
                sh 'pipenv check'
                sh 'pipenv run tox'
            }
        }

        stage('dev') {
            agent {
                docker {
                    image 'governmentpaas/cf-cli'
                    args '-u root'
                }

            }

            environment {
                CLOUDFOUNDRY_API = credentials('CLOUDFOUNDRY_API')
                CF_DOMAIN = credentials('CF_DOMAIN')
                DEV_SECURITY = credentials('DEV_SECURITY')
                CF_USER = credentials('CF_USER')
            }
            steps {

                sh "cf login -a https://${env.CLOUDFOUNDRY_API} --skip-ssl-validation -u ${CF_USER_USR} -p ${CF_USER_PSW} -o rmras -s dev"
                sh 'cf push --no-start ras-collection-instrument-dev-jenkins'
                sh 'cf set-env ras-collection-instrument-dev-jenkins ONS_ENV dev'
                sh 'cf set-env ras-collection-instrument-dev-jenkins RABBITMQ_AMQP CHANGEME'
                sh "cf set-env ras-collection-instrument-dev-jenkins SECURITY_USER_NAME ${env.DEV_SECURITY_USR}"
                sh "cf set-env ras-collection-instrument-dev-jenkins SECURITY_USER_PASSWORD ${env.DEV_SECURITY_PSW}"

                sh "cf set-env ras-collection-instrument-dev-jenkins CASE_SERVICE_PROTOCOL https"
                sh "cf set-env ras-collection-instrument-dev-jenkins CASE_SERVICE_HOST casesvc-dev.${env.CF_DOMAIN}"
                sh "cf set-env ras-collection-instrument-dev-jenkins CASE_SERVICE_PORT 80"

                sh "cf set-env ras-collection-instrument-dev-jenkins COLLECTION_EXERCISE_PROTOCOL https"
                sh "cf set-env ras-collection-instrument-dev-jenkins COLLECTION_EXERCISE_HOST collectionexercisesvc-dev.${env.CF_DOMAIN}"
                sh "cf set-env ras-collection-instrument-dev-jenkins COLLECTION_EXERCISE_PORT 80"

                sh "cf set-env ras-collection-instrument-dev-jenkins RM_SURVEY_SERVICE_PROTOCOL https"
                sh "cf set-env ras-collection-instrument-dev-jenkins RM_SURVEY_SERVICE_HOST surveysvc-dev.${env.CF_DOMAIN}"
                sh "cf set-env ras-collection-instrument-dev-jenkins RM_SURVEY_SERVICE_PORT 80"
                sh 'cf start ras-collection-instrument-dev-jenkins'
            }
        }
    }

    post {
        always {
            cleanWs()
            dir('${env.WORKSPACE}@tmp') {
                deleteDir()
            }
            dir('${env.WORKSPACE}@script') {
                deleteDir()
            }
            dir('${env.WORKSPACE}@script@tmp') {
                deleteDir()
            }
        }
    }
}