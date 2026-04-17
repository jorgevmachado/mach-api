# mach-api
RESTful API, built with FastAPI and async SQLAlchemy.

O projeto foi construído com FastAPI, SQLAlchemy async e arquitetura por domínio, mantendo responsabilidades claras entre rotas, serviços, repositórios e schemas.

```bash
    make install  # Instalação de todas as dependência.
    make format  # Formatação do código (Executa o lint-fix e o lint-format).
    make test # Executa os testes (executa o format o test-app e o test-coverage).
    make dev # Executa o servidor de desenvolvimento.
    make create-migration # Cria uma nova migração para o banco de dados.
    make migrate # Executa as migrações pendentes no banco de dados.
    make test-file # Executa os testes de um arquivo especifico.
```

---

## 1) Arquitetura

1. `app/main.py`: Ponto de entrada da aplicação, onde o FastAPI é instanciado, middlewares são configurados e os routers de cada domínio são incluídos.
2. `app/core/**`: Contém módulos de infraestrutura e utilitários compartilhados, como segurança, cache e logging.
3. `app/domain/**`: Cada subdiretório representa um domínio de negócio, contendo suas próprias rotas, serviços, repositórios, modelos e esquemas.
   1. `app/domain/<dominio>/route.py`: Definição dos endpoints HTTP para cada domínio, utilizando FastAPI e delegando a lógica para os serviços.
   2. `app/domain/<dominio>/schema.py`: Definição dos contratos de dados específicos para cada domínio, incluindo validação e serialização.
   3. `app/domain/<dominio>/services.py`: Implementação da lógica de negócio e orquestração das operações para cada domínio, incluindo cache e tratamento de erros. 
   4. `app/domain/<dominio>/repository.py`: Camada de acesso aos dados, abstração das operações CRUD para cada entidade, utilizando SQLAlchemy async.
   5. `app/domain/<dominio>/business.py`: Implementação das regras de negócio específicas para cada domínio, incluindo validação de regras de negócio e tratamento de exceções.
   6. `app/domain/<dominio>/models.py`: Definição dos modelos de dados para cada domínio, utilizando SQLAlchemy ORM. 
4. `app/models/**`: Definição dos modelos de dados compartilhados entre domínios, incluindo entidades e relacionamentos.
5. `app/shared/**`: Contém módulos de infraestrutura e utilitários compartilhados entre domínios, como configurações, validações e utilitários.
6. `tests/**`: Contém os testes unitários e integração para cada domínio e infraestrutura compartilhada.
 
---

## 2) Principios de atuacao
- Manter separacao de camadas (`route` -> `service` -> `repository` -> `model/schema`).
- Evitar logica de negocio em router.
- Preferir reaproveitar `BaseService`, `BaseRepository` e utilitarios de `core`.
- Garantir tipagem forte (Pydantic + type hints).
- Tratar erros via `handle_service_exception` e padrao de logging.
- Cobrir comportamento com testes de unidade/integracao no dominio afetado.

---

## 3) Limites
| Grupo  | Arquivos                                                                                                                                                                         | Observação                                                                               |
|--------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------|
| models | `app/models/**`                                                                                                                                                                  | Cada entidade deve ser independente                                                      |
| domain | `app/domain/<dominio>/route.py`, `app/domain/<dominio>/schema.py`,  `app/domain/<dominio>/services.py`, `app/domain/<dominio>/repository.py`, `app/domain/<dominio>/business.py` | Cada dominio deve ser independente. Verificar cobertura de testes unitários e integração |
| shared | `app/shared/**`                                                                                                                                                                  | Verificar integridade e consistencia das utilitarios compartilhados                      |
| tests  | `tests/**`                                                                                                                                                                       | Verificar cobertura de testes unitários e integração                                     |

---
## 4) Mapa rapido por tipo de tarefa

### 4.1 Nova rota em dominio existente
1. `app/domain/<dominio>/schema.py`: entrada/saida da rota.
2. `app/domain/<dominio>/service.py`: caso de uso e regras.
3. `app/domain/<dominio>/repository.py`: consulta/persistencia necessaria.
4. `app/domain/<dominio>/route.py`: expor endpoint.
5. `tests/app/domain/<dominio>/test_route.py` e `test_service.py`: validar contrato e regra.

### 4.2 Nova entidade de banco
1. Criar/alterar model em `app/models/`.
2. Ajustar repository/service de dominio dono.
3. Gerar migracao Alembic (`migrations/versions/*`).
4. Adicionar testes de repository e service.

### 4.3 Regra de negocio complexa
- Preferir `business.py` no dominio.
- Cobrir com testes especificos de business.
- Expor somente interface necessaria para service.

### 4.4 Ajuste em autenticacao
- `app/core/security/security.py` para token/hash/current user.
- `app/domain/auth/*` para contrato e fluxo de login/refresh.
- testes em `tests/app/core/security/` e `tests/app/domain/auth/`.

### 4.5 Ajuste em cache
- Cache generico: `app/core/cache/*`.
- Cache de catalogo pokemon: `app/domain/pokemon/cache.py`.
- Validar expiracao/chave com `tests/app/core/cache/*` e `tests/app/domain/pokemon/test_cache.py`.

---

## 5) Regras de implementacao por camada
### 5.1 Route (`route.py`)
- Recebe request/depends e delega para service.
- Sem regra de negocio densa.
- `response_model` explicito.
- Dependencia de autenticacao com `get_current_user` quando endpoint protegido.

### 5.2 Service (`service.py`)
- Orquestra regra, persistencia e integracoes.
- Centraliza cache e tratamento de erro de caso de uso.
- Usa `log_service_success` / `handle_service_exception`.

### 5.3 Repository (`repository.py`)
- Concentra query SQLAlchemy.
- Aproveita `BaseRepository` para list/find/paginar.
- Evita regra de negocio.

### 5.4 Business (`business.py`)
- Regras puras, calculos, normalizacao e decisao de dominio.
- Deve ser altamente testavel sem dependencia de infra.

### 5.5 Schema (`schema.py`)
- Contratos de API e DTOs de camada.
- Validacoes de formato/tipos.
- Evitar acoplamento com session/ORM em schema.

---

## 6) Convencoes de teste
- Local padrao por modulo: `tests/app/domain/<dominio>/` e `tests/app/core/<modulo>/`.
- Para todo ajuste relevante:
  - teste de sucesso;
  - teste de erro/edge case;
  - teste de regressao (quando bugfix).
- Em alteracoes de contrato HTTP, atualizar `test_route.py` correspondente.
- Em alteracoes de query/filtro/paginacao, atualizar `test_repository.py`.

---

## 7) Checklist obrigatorio antes de concluir uma tarefa
- [ ] Alteração foi feita na camada correta.
- [ ] Não houve quebra de contrato de rota sem atualizar schema/teste/docs.
- [ ] Erros são tratados via padrão (`handle_service_exception`/HTTPException apropriada).
- [ ] Logs relevantes foram mantidos/adicionados com contexto.
- [ ] Testes do módulo alterado foram atualizados e executados.
- [ ] Lint (`ruff`) está limpo.
- [ ] Se houve mudanca de banco, migracao foi criada/revisada.

---

## 8) Guardrails para agentes (Não fazer)
- Não mover regra de negocio para `route.py`.
- Não acessar banco diretamente em router.
- Não duplicar logica ja existente em `BaseService`/`BaseRepository`.
- Não introduzir dependencia externa sem necessidade real.
- Não alterar arquivos de geracao automatica sem justificativa (`htmlcov/`, caches).
- Não modificar migracoes historicas ja aplicadas em ambientes compartilhados.

---

## 9) Playbooks prontos
### 9.1 Criar endpoint protegido de consulta
1. Definir schema de filtro/saida em `schema.py`.
2. Criar metodo em `service.py` com `trainer: CurrentTrainer` quando necessario.
3. Reaproveitar `list_all_cached`/`find_one_cached` se aplicavel.
4. Expor rota em `route.py` com dependency de auth.
5. Cobrir `test_route.py` + `test_service.py`.

### 9.2 Bugfix de performance em listagem
1. Revisar `BaseRepository.list_all` e filtros aplicados.
2. Verificar necessidade de cache (`CacheService` / `PokemonCacheService`).
3. Ajustar pagina/filter/order sem quebrar contratos.
4. Cobrir com testes de paginacao e filtro.

---

## 10) Definicao de pronto (DoD) para tarefas automatizadas
Uma tarefa esta pronta quando:
1. implementacao atende requisito funcional;
2. arquitetura e convencoes locais foram respeitadas;
3. testes e lint passaram localmente;
4. documentacao minima (quando aplicavel) foi atualizada;
5. risco de regressao foi coberto com teste novo ou ajuste de teste existente.

---