pipeline {
    agent any

    environment {
        TESTLINK_URL = 'http://testlink-app-1/lib/api/xmlrpc/v1/xmlrpc.php'
    }

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
            description: 'Publica únicamente resultados automatizados producidos y validados por esta ejecución.'
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
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE', message: 'Fallaron las pruebas Maven; se continuará con las demás suites.') {
                    withEnv(['TESTCONTAINERS_HOST_OVERRIDE=host.docker.internal']) {
                        dir('backend') { sh 'bash ./mvnw -B -ntp test' }
                    }
                }
            }
        }

        stage('Frontend - pruebas unitarias') {
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE', message: 'Fallaron las pruebas unitarias del frontend; se continuará con las demás suites.') {
                    dir('frontend') {
                        sh 'npm ci'
                        sh 'CHROME_BIN="$WORKSPACE/qa/jenkins/chrome-headless" npm run test:coverage -- --browsers=ChromeHeadless'
                    }
                }
            }
        }

        stage('Frontend - compilación') {
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE', message: 'Falló la compilación del frontend; se continuará con las demás suites.') {
                    dir('frontend') { sh 'npm run build -- --configuration development' }
                }
            }
        }

        stage('Instalar herramientas de QA') {
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE', message: 'No quedaron listas las dependencias QA; las suites dependientes se marcarán como omitidas.') {
                    sh 'bash qa/jenkins/install-dependencies.sh'
                }
                script {
                    env.QA_DEPS_READY = fileExists('qa/.local/jenkins-deps-ready.flag') ? 'true' : 'false'
                }
            }
        }

        stage('Preparar stack QA aislado en Docker') {
            when { expression { env.QA_DEPS_READY == 'true' } }
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE', message: 'No se pudo preparar el entorno aislado; las suites dependientes se marcarán como omitidas.') {
                    sh 'bash qa/jenkins/prepare-qa.sh'
                }
                script {
                    env.QA_ENV_READY = fileExists('qa/.local/jenkins-ready.flag') ? 'true' : 'false'
                }
            }
        }

        stage('API - Newman') {
            when { expression { env.QA_ENV_READY == 'true' } }
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE', message: 'Newman encontró fallos; se continuará con las demás suites.') {
                    sh 'bash qa/jenkins/run-suite.sh Newman'
                }
            }
        }

        stage('Interfaz - Behave y Selenium') {
            when { expression { env.QA_ENV_READY == 'true' } }
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE', message: 'Behave/Selenium encontró fallos; se continuará con las demás suites.') {
                    sh 'bash qa/jenkins/run-suite.sh Behave'
                }
            }
        }

        stage('Compatibilidad - Playwright') {
            when { expression { env.QA_ENV_READY == 'true' } }
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE', message: 'Playwright encontró fallos; se continuará con las demás suites.') {
                    sh 'bash qa/jenkins/run-suite.sh Compatibility'
                }
            }
        }

        stage('Accesibilidad automatizada - axe-core') {
            when { expression { env.QA_ENV_READY == 'true' } }
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE', message: 'axe-core encontró violaciones o errores de navegación; se continuará con las demás suites.') {
                    sh 'bash qa/jenkins/run-suite.sh Axe'
                }
            }
        }

        stage('K6 - humo') {
            when { expression { env.QA_ENV_READY == 'true' } }
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE', message: 'Falló K6 humo; se continuará con los demás perfiles.') {
                    sh 'bash qa/jenkins/run-suite.sh K6Smoke'
                }
            }
        }

        stage('K6 - línea base') {
            when { expression { env.QA_ENV_READY == 'true' } }
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE', message: 'Falló K6 línea base; se continuará con los demás perfiles.') {
                    sh 'bash qa/jenkins/run-suite.sh K6Baseline'
                }
            }
        }

        stage('K6 - carga moderada') {
            when { expression { env.QA_ENV_READY == 'true' } }
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE', message: 'Falló K6 carga moderada; se continuará con los demás perfiles.') {
                    sh 'bash qa/jenkins/run-suite.sh K6Moderate'
                }
            }
        }

        stage('K6 - estrés progresivo') {
            when { expression { env.QA_ENV_READY == 'true' } }
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE', message: 'Falló K6 estrés progresivo; se continuará con los demás perfiles.') {
                    sh 'bash qa/jenkins/run-suite.sh K6Stress'
                }
            }
        }

        stage('K6 - pico repentino') {
            when { expression { env.QA_ENV_READY == 'true' } }
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE', message: 'Falló K6 pico repentino; se continuará con los demás perfiles.') {
                    sh 'bash qa/jenkins/run-suite.sh K6Spike'
                }
            }
        }

        stage('K6 - carga sostenida') {
            when { expression { env.QA_ENV_READY == 'true' } }
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE', message: 'Falló K6 carga sostenida; se continuará con TestLink.') {
                    sh 'bash qa/jenkins/run-suite.sh K6Sustained'
                }
            }
        }

        stage('Generar resumen automatizado para TestLink') {
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE', message: 'No se pudo generar el resumen de esta corrida para TestLink.') {
                    sh 'bash qa/jenkins/generate-summary.sh'
                }
            }
        }

        stage('Validar resumen TestLink') {
            when { expression { fileExists('qa/testlink/results/current-run.json') || params.PUBLICAR_RESULTADOS_TESTLINK } }
            steps {
                script {
                    if (!fileExists('qa/testlink/results/current-run.json')) {
                        error('No hay resumen de esta corrida; no se enviará nada a TestLink.')
                    }
                    sh 'python3 qa/testlink/publish_results.py --results qa/testlink/results/current-run.json'
                }
            }
        }

        stage('Publicar resultados en TestLink') {
            when { expression { params.PUBLICAR_RESULTADOS_TESTLINK && fileExists('qa/testlink/results/current-run.json') } }
            steps {
                script {
                    if (!fileExists('qa/testlink/results/case-id-map.json')) {
                        error('Publicación cancelada: falta el mapa de IDs de TestLink.')
                    }
                    if (!env.TESTLINK_URL?.trim()) {
                        error('Publicación cancelada: configure TESTLINK_URL en Jenkins.')
                    }
                }
                withCredentials([string(credentialsId: 'testlink-devkey', variable: 'TESTLINK_DEVKEY')]) {
                    sh 'python3 qa/testlink/publish_results.py --results qa/testlink/results/current-run.json --publish'
                }
            }
        }
    }

    post {
        always {
            junit testResults: 'backend/target/surefire-reports/TEST-*.xml', allowEmptyResults: true
            junit testResults: 'qa/artifacts/**/*.xml', allowEmptyResults: true
            archiveArtifacts artifacts: 'backend/target/surefire-reports/**,frontend/coverage/**,frontend/dist/**,qa/artifacts/**,qa/testlink/results/current-run.json,qa/testlink/results/publication-report.json', allowEmptyArchive: true
            sh 'if [ -f qa/.local/jenkins-run.json ]; then bash qa/jenkins/cleanup-qa.sh; fi'
        }
    }
}
