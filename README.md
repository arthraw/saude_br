Data Pipeline: Ecossistema de Saúde SUS 🏥
======

Este projeto consiste em um pipeline de dados desenvolvida em PySpark e Delta Lake, focado no processamento de estabelecimentos de saúde e estoques de medicamentos do SUS. A arquitetura segue o padrão Medallion Architecture, garantindo qualidade, histórico (SCD Tipo 2) e performance.

🏗️ Arquitetura do Projeto
======
O pipeline é dividido em três camadas principais dentro do Databricks:

**Bronze (Raw):** Ingestão dos dados brutos em formato JSON vindos da [DEMAS - API de Dados Abertos](https://apidadosabertos.saude.gov.br/v1/).

**Silver (Trusted):** * Casting de tipos e normalização de nomes.

- Tratamento de duplicidade total.

- Implementação de SCD Tipo 2 para rastreamento histórico de mudanças nos estabelecimentos.

**Gold (Refined):**

- Modelagem dimensional em Galaxy Schema.

- Criação de tabelas Fato (fact_estabelecimento, fact_estoque_medicamento).

- Dimensões Conformadas (dim_localizacao, dim_calendario).

🛠️ Tecnologias Utilizadas
======

- **Linguagem**: Python (PySpark).

- **Armazenamento**: Delta Lake (Acid Compliance).

- **Orquestração**: Apache Airflow.

- **Modelagem**: Star Schema / Galaxy Schema.

- **Ingestão**: Airbyte.

📊 Modelo de Dados (Galaxy Schema)
======
O projeto utiliza múltiplas tabelas fato que compartilham as mesmas dimensões para permitir cruzamentos analíticos complexos.

- Fato Estabelecimento: Métricas de infraestrutura (Centro cirúrgico, atendimento SUS).

- Fato Estoque: Saldo de medicamentos por lote e validade.

- Dimensões: Estabelecimento, Localização (Enriquecida), Medicamento e Calendário.