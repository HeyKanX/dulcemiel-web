pipeline {
    agent any

    options {
        skipDefaultCheckout(true)
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '20'))
        timestamps()
    }

    parameters {
        booleanParam(
            name: 'PUBLICAR_RESULTADOS_TESTLINK',
            defaultValue: false,
            description: 'Publica únicamente resultados producidos y validados por esta ejecución.'
        )
    }

    stages {
        stage('Checkout') {
            steps {
                deleteDir()
                checkout scm
            }
        }

        stage('Backend - pruebas Maven') {
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE', message: 'Fallaron las pruebas Maven del backend; se continuará para recopilar los demás resultados.') {
                    script {
                        if (isUnix()) {
                            dir('backend') { sh './mvnw -B -ntp test' }
                        } else {
                            dir('backend') { bat 'mvnw.cmd -B -ntp test' }
                        }
                    }
                }
            }
        }

        stage('Frontend - pruebas unitarias') {
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE', message: 'Fallaron las pruebas unitarias del frontend; se continuará con las etapas restantes.') {
                    script {
                        if (isUnix()) {
                            dir('frontend') {
                                sh 'npm ci'
                                sh 'npm run test:coverage -- --browsers=ChromeHeadless'
                            }
                        } else {
                            dir('frontend') {
                                bat 'npm ci'
                                bat 'npm run test:coverage -- --browsers=ChromeHeadless'
                            }
                        }
                    }
                }
            }
        }

        stage('Frontend - compilación') {
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE', message: 'Falló la compilación del frontend; se continuará con la validación de resultados.') {
                    script {
                        if (isUnix()) {
                            dir('frontend') { sh 'npm run build' }
                        } else {
                            dir('frontend') { bat 'npm run build' }
                        }
                    }
                }
            }
        }

        stage('Validar resumen TestLink') {
            when {
                expression { fileExists('qa/testlink/results/current-run.json') || params.PUBLICAR_RESULTADOS_TESTLINK }
            }
            steps {
                script {
                    if (!fileExists('qa/testlink/results/current-run.json')) {
                        error('No hay resumen de esta corrida; no se publicará nada en TestLink.')
                    }
                    if (isUnix()) {
                        sh 'python3 qa/testlink/publish_results.py --results qa/testlink/results/current-run.json'
                    } else {
                        bat 'py qa\\testlink\\publish_results.py --results qa\\testlink\\results\\current-run.json'
                    }
                    env.TESTLINK_SUMMARY_VALID = 'true'
                }
            }
        }

        stage('Publicar resultados en TestLink') {
            when {
                expression { params.PUBLICAR_RESULTADOS_TESTLINK && env.TESTLINK_SUMMARY_VALID == 'true' }
            }
            steps {
                script {
                    def requiredFiles = [
                        'qa/testlink/publish_results.py',
                        'qa/testlink/results/case-id-map.json',
                        'qa/testlink/results/current-run.json'
                    ]
                    def missingFiles = requiredFiles.findAll { !fileExists(it) }
                    if (!missingFiles.isEmpty()) {
                        error('Publicación cancelada: faltan artefactos de esta ejecución: ' + missingFiles.join(', '))
                    }
                    if (!env.TESTLINK_URL?.trim()) {
                        error('Publicación cancelada: configure TESTLINK_URL en Jenkins.')
                    }
                }

                withCredentials([string(credentialsId: 'testlink-devkey', variable: 'TESTLINK_DEVKEY')]) {
                    script {
                        if (isUnix()) {
                            sh 'python3 qa/testlink/publish_results.py --results qa/testlink/results/current-run.json --publish'
                        } else {
                            bat 'py qa\\testlink\\publish_results.py --results qa\\testlink\\results\\current-run.json --publish'
                        }
                    }
                }
            }
        }
    }

    post {
        always {
            junit testResults: 'backend/target/surefire-reports/TEST-*.xml', allowEmptyResults: true
            archiveArtifacts artifacts: 'backend/target/surefire-reports/**,frontend/coverage/**,frontend/dist/**,qa/testlink/results/publication-report.json', allowEmptyArchive: true
        }
    }
}
