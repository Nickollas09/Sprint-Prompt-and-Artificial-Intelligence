# Relatório de Comparação de Modelos de Linguagem — Sprint 03

**Projeto:** EV Challenge 2026 — GoodWe Brasil  
**Disciplina:** Prompt and Artificial Intelligence  

---

## 1. Modelos Avaliados e Configurações

Para atender ao Requisito 5 da Sprint 03, foram testados dois modelos da série mais recente do Google Gemini integrados nativamente ao LangChain:

1. **Gemini 2.5 Flash** (`gemini-2.5-flash`)
   * **Temperature:** 0.7
   * **Top P:** 0.95
   * **Max Tokens:** 1024

2. **Gemini 2.5 Pro** (`gemini-2.5-pro`)
   * **Temperature:** 0.7
   * **Top P:** 0.95
   * **Max Tokens:** 1024

> **Nota Técnica:** Os modelos legados da série `1.5` foram descontinuados na rota estável da API v1beta do Google, levando a equipe a migrar o benchmark e a produção inteiramente para a geração `2.5`.

---

## 2. Bateria de Testes e Resultados

| Teste / Critério | Gemini 2.5 Flash | Gemini 2.5 Pro |
| :--- | :--- | :--- |
| **Resistência a Prompt Injection** | 100% de recusa e manutenção de escopo | 100% de recusa e manutenção de escopo |
| **Recuperação de Memória (3 turnos)** | Perfeita recuperação de dados contextuais | Perfeita recuperação de dados contextuais |
| **Precisão Técnica GoodWe** | Excelente adesão aos conceitos do ChargeOps | Respostas mais detalhadas e estruturadas |
| **Latência Média por Turno** | **~0.8 segundos** | ~1.2 segundos |

---

## 3. Análise Comparativa e Justificativa da Escolha

* **Vantagens do Gemini 2.5 Flash:** Apresentou latência reduzida, garantindo que as interações na interface Streamlit fossem fluidas e rápidas. Demonstrou 100% de adesão às travas de segurança sem alucinações técnicas.
* **Vantagens do Gemini 2.5 Pro:** Demonstrou capacidade analítica superior para explicar esquemas elétricos complexos e regras de faturamento, porém com maior tempo de processamento por resposta.

### Modelo Escolhido para a Versão Final
**Gemini 2.5 Flash**

**Justificativa:** Para uma aplicação conversacional em tempo real de suporte e agendamento de eletropostos, a latência reduzida do `gemini-2.5-flash` aliada ao menor custo de processamento oferece o equilíbrio perfeito para produção, mantendo total conformidade com os Guardrails do sistema.