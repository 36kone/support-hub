# Support System

Sistema de suporte interno desenvolvido como um projeto de estudo para
explorar uma arquitetura diferente de uma aplicação FastAPI tradicional
e, principalmente, para experimentar processamento assíncrono real com
**Celery + RabbitMQ + Redis**.

O projeto será construído como um **Modular Monolith**, combinando
conceitos de **Clean Architecture / Hexagonal Architecture**,
organização por domínio e um **CQRS leve**, sem transformar a aplicação
em uma implementação excessivamente acadêmica.

O objetivo não é apenas construir um sistema de chamados funcional, mas
criar um ambiente para experimentar decisões arquiteturais que podem ser
úteis em sistemas backend de maior porte.

------------------------------------------------------------------------

## Objetivos

Este projeto tem alguns objetivos principais:

-   Construir um sistema de chamados para uso interno.
-   Experimentar uma organização de código diferente de
    `Controller -> Service -> Repository`.
-   Organizar o sistema por **módulos de negócio**, em vez de apenas por
    tipo técnico.
-   Aprender e utilizar **Celery** de forma real.
-   Utilizar **RabbitMQ** como broker de mensagens.
-   Utilizar **Redis** para cache, sessões, locks, resultados e
    comunicação auxiliar.
-   Utilizar **MinIO** como object storage.
-   Utilizar **PostgreSQL** como banco de dados principal.
-   Experimentar **eventos de domínio**.
-   Separar regras de negócio de detalhes de infraestrutura.
-   Experimentar **Use Cases / Commands / Queries**.
-   Criar tarefas assíncronas que não dependam de uma requisição HTTP.
-   Trabalhar com WebSockets para atualizações em tempo real.
-   Criar uma arquitetura que permita trocar detalhes de infraestrutura
    sem alterar o domínio.

------------------------------------------------------------------------

# Stack

## Backend

-   Python
-   FastAPI
-   Pydantic
-   SQLAlchemy
-   Alembic

## Banco de dados

-   PostgreSQL

## Mensageria e processamento assíncrono

-   Celery
-   RabbitMQ

## Cache e dados temporários

-   Redis

## Object Storage

-   MinIO

## Comunicação em tempo real

-   WebSockets

## Infraestrutura

-   Docker
-   Docker Compose

------------------------------------------------------------------------

# Arquitetura

O projeto será desenvolvido como um **Modular Monolith**.

A aplicação continua sendo um único deploy, mas seus módulos são
separados por responsabilidade de negócio.

A ideia principal é:

``` text
                    ┌─────────────────┐
                    │     FastAPI     │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   Application   │
                    │     Layer       │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
        PostgreSQL         Events          MinIO
                             │
                             ▼
                         RabbitMQ
                             │
                             ▼
                     Celery Workers
                             │
                  ┌──────────┼──────────┐
                  ▼          ▼          ▼
                Redis    PostgreSQL    MinIO
                  │
                  ▼
             WebSocket
```

O ponto mais importante é que **a regra de negócio não deve depender
diretamente de FastAPI, SQLAlchemy, Celery, Redis, RabbitMQ ou MinIO**.

Essas tecnologias são detalhes de infraestrutura.

------------------------------------------------------------------------

# Organização por módulos

Em vez de organizar toda a aplicação assim:

``` text
services/
repositories/
models/
schemas/
controllers/
```

o projeto será organizado primeiro pelo domínio:

``` text
modules/
├── auth/
├── users/
├── tickets/
├── notifications/
└── attachments/
```

Cada módulo contém as responsabilidades relacionadas àquele contexto.

Por exemplo:

``` text
tickets/
├── domain/
├── application/
├── infrastructure/
├── presentation/
└── tasks/
```

Isso permite encontrar tudo relacionado a tickets dentro do próprio
módulo.

------------------------------------------------------------------------

# Estrutura de diretórios

A estrutura inicial proposta é:

``` text
app/
│
├── modules/
│   │
│   ├── auth/
│   │   ├── domain/
│   │   │   ├── entities/
│   │   │   ├── enums/
│   │   │   └── repositories/
│   │   │
│   │   ├── application/
│   │   │   ├── commands/
│   │   │   └── queries/
│   │   │
│   │   ├── infrastructure/
│   │   │   ├── models/
│   │   │   └── repositories/
│   │   │
│   │   └── presentation/
│   │       ├── controllers/
│   │       └── schemas/
│   │
│   ├── users/
│   │   ├── domain/
│   │   ├── application/
│   │   ├── infrastructure/
│   │   └── presentation/
│   │
│   ├── tickets/
│   │   ├── domain/
│   │   │   ├── entities/
│   │   │   ├── enums/
│   │   │   └── repositories/
│   │   │
│   │   ├── application/
│   │   │   ├── ticket_service.py
│   │   │   ├── ticket_reader.py
│   │   │   ├── ticket_writer.py
│   │   │   ├── ports/
│   │   │   │   └── user_reader.py
│   │   │   └── workflows/
│   │   │       └── transfer_ticket.py
│   │   │
│   │   ├── infrastructure/
│   │   │   ├── models/
│   │   │   └── repositories/
│   │   │       └── sqlalchemy_ticket_repository.py
│   │   │
│   │   ├── presentation/
│   │   │   ├── controllers/
│   │   │   └── schemas/
│   │   │
│   │   └── tasks/
│   │       ├── notify_ticket_created.py
│   │       └── generate_ticket_report.py
│   │
│   ├── notifications/
│   │   ├── domain/
│   │   ├── application/
│   │   ├── infrastructure/
│   │   └── presentation/
│   │
│   └── attachments/
│       ├── domain/
│       ├── application/
│       ├── infrastructure/
│       └── presentation/
│
├── infrastructure/
│   │
│   ├── database/
│   │   ├── engine.py
│   │   ├── session.py
│   │   └── base.py
│   │
│   ├── celery/
│   │   ├── app.py
│   │   ├── config.py
│   │   └── base_task.py
│   │
│   ├── redis/
│   │   └── client.py
│   │
│   ├── rabbitmq/
│   │   └── connection.py
│   │
│   ├── minio/
│   │   ├── client.py
│   │   └── storage.py
│   │
│   └── websocket/
│       ├── manager.py
│       └── pubsub.py
│
├── shared/
│   ├── domain/
│   │   ├── entity.py
│   │   └── event.py
│   ├── exceptions/
│   └── utils/
│
└── main.py
```

A estrutura pode evoluir conforme o sistema crescer. A ideia é evitar
criar abstrações antecipadamente apenas porque a arquitetura permite.

------------------------------------------------------------------------

# Camadas

## Domain

A camada de domínio contém os conceitos e regras centrais do negócio.

Exemplos:

``` text
Ticket
TicketStatus
TicketPriority
TicketCreated
TicketAssigned
TicketClosed
```

O domínio não deve conhecer:

-   FastAPI
-   SQLAlchemy
-   Celery
-   RabbitMQ
-   Redis
-   MinIO
-   HTTP
-   detalhes de banco de dados

Exemplo:

``` python
@dataclass
class Ticket:
    id: UUID
    title: str
    description: str
    status: TicketStatus
    priority: TicketPriority
```

------------------------------------------------------------------------

# Application

A camada de aplicação representa os **casos de uso** e a orquestração do
sistema.

O projeto não tratará `Service`, `Reader`, `Writer`, `Command` e `Query`
como camadas obrigatórias empilhadas. Eles representam responsabilidades
diferentes e devem ser utilizados quando fizerem sentido.

Uma regra prática:

``` text
Use Case / Service → o que a aplicação precisa fazer
Repository         → como persistir/recuperar entidades
Reader             → organização de operações de leitura
Writer             → organização de operações de escrita
```

Para operações mais complexas, o módulo pode possuir um Service ou Use
Case explícito:

``` text
application/
├── ticket_service.py
├── ticket_reader.py
├── ticket_writer.py
├── ports/
└── workflows/
```

Para um módulo pequeno, também é perfeitamente válido começar apenas
com:

``` text
application/
└── ticket_service.py
```

e separar responsabilidades posteriormente quando a complexidade
justificar.

------------------------------------------------------------------------

# Use Cases / Services

Use Cases representam operações da aplicação e podem orquestrar domínio,
repositories, eventos e ports.

Exemplo:

``` python
class TicketService:

    def __init__(
        self,
        reader,
        writer,
        event_publisher,
    ):
        self.reader = reader
        self.writer = writer
        self.event_publisher = event_publisher

    async def close(self, ticket_id, user_id):
        ticket = await self.reader.get_by_id(ticket_id)

        if ticket is None:
            raise TicketNotFound()

        ticket.close(user_id)

        await self.writer.update(ticket)

        await self.event_publisher.publish(
            TicketClosed(ticket.id)
        )

        return ticket
```

O `TicketService` não precisa saber se o repository usa SQLAlchemy,
PostgreSQL ou outra tecnologia.

Também não é necessário criar um Service apenas para repassar uma
chamada diretamente para um Repository. Para uma leitura trivial, por
exemplo:

``` text
Controller
    ↓
TicketReader
    ↓
Repository
```

pode ser suficiente.

------------------------------------------------------------------------

# Commands

Commands representam operações que alteram o estado da aplicação.

Exemplos:

``` text
CreateTicket
AssignTicket
CloseTicket
ReopenTicket
AddComment
AddAttachment
```

Commands podem ser implementados como Use Cases independentes ou
agrupados em um Service quando isso tornar o módulo mais simples.

Fluxo:

``` text
HTTP Request
     │
     ▼
Controller
     │
     ▼
Application Use Case / Service
     │
     ├── Repository
     └── Event Publisher
```

------------------------------------------------------------------------

# Queries

Queries são operações de leitura.

Exemplos:

``` text
GetTicket
ListTickets
GetUserTickets
ListTicketComments
SearchTickets
```

Queries não precisam obrigatoriamente possuir uma classe por operação.

Quando houver poucas operações, elas podem ser agrupadas em um Reader:

``` text
application/
└── ticket_reader.py
```

Por exemplo:

``` python
class TicketReader:

    async def get_by_id(self, ticket_id):
        ...

    async def get_by_user(self, user_id):
        ...

    async def search(self, filters):
        ...

    async def list(self, pagination):
        ...
```

Da mesma forma, operações de escrita podem ser agrupadas em um Writer:

``` python
class TicketWriter:

    async def create(self, ticket):
        ...

    async def update(self, ticket):
        ...

    async def delete(self, ticket_id):
        ...

    async def assign(self, ticket_id, user_id):
        ...

    async def close(self, ticket_id):
        ...
```

Isso é uma organização interna da aplicação, não uma regra arquitetural
obrigatória.

------------------------------------------------------------------------

# Repository vs Reader / Writer

É importante não confundir essas responsabilidades.

**Repository** é uma abstração de persistência. Ele define como o
domínio ou a aplicação pode acessar e persistir seus dados.

**Reader** e **Writer** são uma forma de organizar operações de leitura
e escrita na aplicação. Eles representam o que a aplicação quer fazer
com esses dados.

Exemplo:

``` text
TicketReader
    │
    └── get_by_id()
             │
             ▼
      TicketRepository
             │
             ▼
      PostgreSQL
```

Ou:

``` text
TicketService
    │
    ├── TicketReader
    │      └── TicketRepository
    │
    └── TicketWriter
           └── TicketRepository
```

Não é necessário criar `Repository + Reader + Writer + Service` para
toda operação. A estrutura deve acompanhar a complexidade real do
módulo.

------------------------------------------------------------------------

# Cross-Domain / Cross-Module

Um módulo pode precisar de informações ou capacidades pertencentes a
outro módulo.

Por exemplo, `Tickets` pode precisar consultar um usuário pertencente ao
módulo `Users`.

A regra principal é:

> O módulo consumidor define a abstração daquilo que ele precisa.

Assim, em vez de `Tickets` depender diretamente de detalhes internos de
`Users`, ele pode definir um port:

``` text
tickets/
└── application/
    └── ports/
        └── user_reader.py
```

Exemplo:

``` python
class UserReader(Protocol):

    async def get_by_id(
        self,
        user_id: UUID,
    ) -> UserData | None:
        ...
```

O `TicketService` depende de `UserReader`:

``` text
TicketService
     │
     ├── TicketReader
     ├── TicketWriter
     └── UserReader
              │
              ▼
       Users adapter
              │
              ▼
       Users Repository
```

O ponto importante é que o módulo `Tickets` não precisa conhecer a
implementação interna de `Users`.

------------------------------------------------------------------------

# Cross-Domain Events

Quando a comunicação representa um acontecimento, eventos podem ser mais
adequados do que uma chamada direta entre módulos.

Exemplo:

``` text
CreateTicket
      │
      ▼
TicketCreated
      │
      ├── Notification
      ├── Audit
      ├── Metrics
      └── WebSocket
```

Nesse cenário, `Tickets` não precisa chamar diretamente
`NotificationService`.

O evento representa:

> "Um ticket foi criado."

E outros componentes decidem o que fazer com esse acontecimento.

Eventos concretos pertencem ao módulo que os produz:

``` text
tickets/
└── domain/
    └── events/
        └── ticket_created.py
```

Conceitos realmente genéricos, como uma abstração de `DomainEvent` ou
`EventPublisher`, podem ficar em `shared/` quando forem utilizados por
vários módulos.

------------------------------------------------------------------------

# Cross-Domain Workflows

Nem todo fluxo entre módulos deve ser transformado em evento.

Quando existe um workflow que realmente coordena várias
responsabilidades, pode existir um orchestrator na camada de aplicação:

``` text
application/
└── workflows/
    └── transfer_ticket.py
```

Exemplo conceitual:

``` text
TransferTicketWorkflow
       │
       ├── TicketService
       ├── UserReader
       └── EventPublisher
```

Isso deve ser utilizado quando existe uma operação de negócio que
realmente coordena múltiplos módulos.

Evitar criar uma cadeia arbitrária como:

``` text
UseCase A
   ↓
UseCase B
   ↓
UseCase C
   ↓
UseCase D
```

porque isso tende a criar um grafo de dependências difícil de manter.

------------------------------------------------------------------------

# Shared

`shared/` **não será utilizado como uma pasta para colocar qualquer
coisa que seja compartilhada entre módulos**.

Ele deve conter apenas conceitos realmente neutros e independentes de um
domínio específico.

Exemplos aceitáveis:

``` text
shared/
├── domain/
│   ├── entity.py
│   ├── event.py
│   └── event_bus.py
├── exceptions/
└── utils/
```

Evitar:

``` text
shared/
├── user_service.py
├── ticket_service.py
├── notification_service.py
└── cross_domain_service.py
```

Esses componentes pertencem aos seus respectivos módulos.

A regra é:

> Shared contém conceitos genéricos; regras de negócio continuam
> próximas do domínio que possui aquela responsabilidade.

------------------------------------------------------------------------

# Infrastructure

A infraestrutura contém os detalhes técnicos da aplicação.

``` text
infrastructure/
├── database/
├── celery/
├── redis/
├── rabbitmq/
├── minio/
└── websocket/
```

A regra utilizada será:

> Infrastructure contém aquilo que poderia ser substituído por outra
> tecnologia sem alterar as regras de negócio.

Exemplos:

``` text
PostgreSQL  → Infrastructure
SQLAlchemy  → Infrastructure
Celery      → Infrastructure
RabbitMQ    → Infrastructure
Redis       → Infrastructure
MinIO       → Infrastructure
```

Enquanto:

``` text
Ticket
CreateTicket
CloseTicket
TicketStatus
TicketPriority
TicketCreated
```

pertencem ao domínio/aplicação.

------------------------------------------------------------------------

# Database

O PostgreSQL será o banco principal da aplicação.

A infraestrutura de banco será centralizada:

``` text
infrastructure/database/
├── engine.py
├── session.py
└── base.py
```

Os models do SQLAlchemy ficam associados aos módulos:

``` text
tickets/
└── infrastructure/
    └── models/
        └── ticket_model.py
```

A ideia é separar a entidade de domínio do model de persistência.

``` text
Domain Entity
      ↕
Repository
      ↕
SQLAlchemy Model
      ↕
PostgreSQL
```

------------------------------------------------------------------------

# Repository

Repositories serão utilizados quando fizer sentido para o domínio.

A interface pode viver no domínio:

``` text
tickets/
└── domain/
    └── repositories/
        └── ticket_repository.py
```

Enquanto a implementação fica na infraestrutura:

``` text
tickets/
└── infrastructure/
    └── repositories/
        └── sqlalchemy_ticket_repository.py
```

Assim:

``` text
Application
     │
     ▼
TicketRepository
     │
     ▼
SQLAlchemyTicketRepository
     │
     ▼
PostgreSQL
```

O domínio não precisa conhecer SQLAlchemy.

------------------------------------------------------------------------

# Celery

Um dos principais objetivos do projeto é aprender Celery de forma real.

Celery não será utilizado simplesmente como um substituto para:

``` python
BackgroundTasks()
```

A ideia é utilizar uma fila de tarefas distribuídas.

Fluxo:

``` text
Application
     │
     ▼
Celery
     │
     ▼
RabbitMQ
     │
     ▼
Celery Worker
     │
     ▼
Task
```

Isso permite executar tarefas independentemente de uma requisição HTTP.

------------------------------------------------------------------------

# Por que Celery?

O `BackgroundTasks` do FastAPI é útil para tarefas simples associadas ao
ciclo de vida de uma requisição.

Porém, ele não é um sistema completo de processamento distribuído.

Com Celery, uma tarefa pode:

-   ser colocada em uma fila;
-   aguardar processamento;
-   ser executada por um worker separado;
-   ser reexecutada;
-   possuir retry;
-   ter prioridade;
-   ser distribuída entre múltiplos workers;
-   continuar existindo independentemente do processo HTTP.

Isso é especialmente útil quando uma operação pode ser iniciada por:

``` text
HTTP
WebSocket
CLI
Scheduler
Outro worker
Evento
```

O Use Case não precisa depender de uma instância de `BackgroundTasks`.

------------------------------------------------------------------------

# RabbitMQ

RabbitMQ será utilizado como **broker do Celery**.

Fluxo:

``` text
Application
     │
     │ enqueue task
     ▼
RabbitMQ
     │
     ▼
Celery Worker
```

RabbitMQ será responsável por transportar as mensagens entre produtores
e consumidores.

------------------------------------------------------------------------

# Redis

Redis terá responsabilidades diferentes de RabbitMQ.

Possíveis usos:

``` text
Redis
├── Sessions
├── Cache
├── Rate Limiting
├── Locks
├── Celery Result Backend
└── Pub/Sub
```

A intenção é não utilizar Redis como substituto de tudo.

RabbitMQ será utilizado principalmente como broker de mensagens do
Celery, enquanto Redis será utilizado para dados temporários, cache e
mecanismos auxiliares.

------------------------------------------------------------------------

# MinIO

MinIO será utilizado como object storage.

Arquivos não serão armazenados diretamente no PostgreSQL.

Por exemplo, ao anexar um arquivo:

``` text
Client
  │
  ▼
FastAPI
  │
  ▼
Attachment Use Case
  │
  ├── MinIO → arquivo
  │
  └── PostgreSQL → metadados
```

O PostgreSQL pode armazenar:

``` text
id
ticket_id
filename
object_key
content_type
size
uploaded_by
created_at
```

Enquanto o conteúdo real fica no MinIO.

------------------------------------------------------------------------

# Abstração de Storage

A aplicação pode depender de uma abstração:

``` python
class FileStorage(Protocol):

    async def upload(
        self,
        file: BinaryIO,
        filename: str,
        content_type: str,
    ) -> str:
        ...
```

E a infraestrutura fornece:

``` python
class MinioFileStorage:
    ...
```

Fluxo:

``` text
Application
     │
     ▼
FileStorage
     │
     ▼
MinIO
```

Isso permite trocar MinIO por S3, por exemplo, sem alterar a regra de
negócio.

------------------------------------------------------------------------

# WebSockets

WebSockets serão utilizados para atualizações em tempo real.

Um exemplo:

``` text
Ticket atualizado
       │
       ▼
Event
       │
       ▼
Redis Pub/Sub
       │
       ▼
WebSocket Manager
       │
       ▼
Clientes conectados
```

Isso permite que usuários recebam eventos como:

``` text
TicketAssigned
TicketStatusChanged
TicketCommentAdded
```

sem precisar ficar fazendo polling constantemente.

------------------------------------------------------------------------

# Eventos

O projeto utilizará eventos para representar acontecimentos importantes.

Exemplos:

``` text
TicketCreated
TicketAssigned
TicketStatusChanged
TicketCommentAdded
TicketClosed
TicketAttachmentAdded
```

Um evento pode gerar várias ações:

``` text
TicketCreated
     │
     ├── Notificação
     ├── Auditoria
     ├── Métricas
     └── WebSocket
```

A ideia é reduzir o acoplamento entre essas ações.

------------------------------------------------------------------------

# Exemplo: criação de ticket

Um fluxo completo pode ser:

``` text
POST /tickets
       │
       ▼
TicketController
       │
       ▼
CreateTicket
       │
       ├── TicketRepository
       │       │
       │       ▼
       │   PostgreSQL
       │
       └── TicketCreated
                  │
                  ▼
               RabbitMQ
                  │
                  ▼
            Celery Worker
                  │
          ┌───────┴────────┐
          ▼                ▼
   Notification       WebSocket
```

O request HTTP não precisa esperar todas essas operações terminarem.

------------------------------------------------------------------------

# Exemplo: relatório

Um dos casos de uso para testar Celery será a geração de relatórios.

Em vez de:

``` text
GET /reports/tickets

     ↓

Gerar PDF

     ↓

Esperar 30 segundos

     ↓

Retornar arquivo
```

a aplicação poderá fazer:

``` text
POST /reports/tickets
       │
       ▼
CreateTicketReport
       │
       ▼
Celery
       │
       ▼
RabbitMQ
       │
       ▼
Worker
       │
       ├── PostgreSQL
       ├── gera PDF
       └── MinIO
```

A API retorna:

``` text
202 Accepted
```

com um identificador do job.

Depois o cliente pode consultar:

``` text
GET /reports/{job_id}
```

Estados possíveis:

``` text
PENDING
PROCESSING
COMPLETED
FAILED
```

Quando finalizar:

``` text
Celery Worker
      │
      ▼
MinIO
      │
      ▼
report.pdf
```

------------------------------------------------------------------------

# Domínio do sistema

O sistema será um sistema de suporte interno.

Os principais conceitos serão:

``` text
User
UserSession

Ticket
TicketUser
TicketComment
TicketAttachment
TicketStatusHistory
```

------------------------------------------------------------------------

# User

Usuários do sistema.

Exemplo:

``` text
users
-----
id
name
email
password_hash
is_active
created_at
updated_at
```

------------------------------------------------------------------------

# User Session

Sessões de autenticação.

``` text
user_sessions
-------------
id
user_id
token_hash
expires_at
created_at
revoked_at
```

Redis poderá ser utilizado para acelerar ou controlar sessões, enquanto
o PostgreSQL pode manter o registro persistente das sessões.

------------------------------------------------------------------------

# Ticket

Representa um chamado.

``` text
tickets
-------
id
title
description
status
priority
creator_id
assigned_at
created_at
updated_at
closed_at
```

Possíveis status:

``` text
OPEN
IN_PROGRESS
WAITING
RESOLVED
CLOSED
```

Possíveis prioridades:

``` text
LOW
MEDIUM
HIGH
CRITICAL
```

------------------------------------------------------------------------

# Ticket Users

Um ticket pode possuir vários usuários relacionados.

``` text
ticket_users
------------
ticket_id
user_id
role
created_at
```

Possíveis roles:

``` text
REQUESTER
ASSIGNEE
WATCHER
```

Isso permite cenários como:

``` text
Ticket
 ├── Requester
 ├── Assignee
 └── Watchers
```

------------------------------------------------------------------------

# Ticket Comments

Comentários pertencentes a um ticket.

``` text
ticket_comments
---------------
id
ticket_id
user_id
content
created_at
```

------------------------------------------------------------------------

# Ticket Attachments

Anexos relacionados aos tickets.

``` text
ticket_attachments
------------------
id
ticket_id
uploaded_by
object_key
filename
content_type
size
created_at
```

O arquivo fica no MinIO.

O banco mantém somente os metadados necessários.

------------------------------------------------------------------------

# Ticket Status History

Histórico de alterações do ticket.

``` text
ticket_status_history
---------------------
id
ticket_id
user_id
old_status
new_status
created_at
```

Isso permite visualizar:

``` text
OPEN
  ↓
IN_PROGRESS
  ↓
WAITING
  ↓
IN_PROGRESS
  ↓
RESOLVED
  ↓
CLOSED
```

------------------------------------------------------------------------

# Notificações

O módulo de notificações pode ser responsável por informar usuários
sobre acontecimentos importantes.

Exemplos:

``` text
Ticket criado
Ticket atribuído
Novo comentário
Ticket resolvido
Ticket fechado
```

O fluxo pode ser:

``` text
TicketCreated
      │
      ▼
Celery
      │
      ▼
NotificationService
      │
      ├── Database
      ├── Redis
      └── WebSocket
```

------------------------------------------------------------------------

# Tasks

Tasks do Celery ficam próximas do módulo que possui o contexto da
tarefa.

Por exemplo:

``` text
tickets/
└── tasks/
    ├── notify_ticket_created.py
    └── generate_ticket_report.py
```

A infraestrutura global contém a configuração do Celery:

``` text
infrastructure/
└── celery/
    ├── app.py
    ├── config.py
    └── base_task.py
```

Enquanto as tasks pertencem ao contexto do negócio.

Essa separação evita transformar `infrastructure/celery/` em uma pasta
gigante com todas as tasks da aplicação.

------------------------------------------------------------------------

# Exemplo de task

Conceitualmente:

``` python
@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def notify_ticket_created(self, ticket_id: str):
    ...
```

A task recebe somente aquilo que precisa para processar o trabalho.

Uma boa prática será evitar passar objetos complexos ou sessões do
SQLAlchemy para dentro da task.

Prefira:

``` python
notify_ticket_created.delay(ticket_id)
```

em vez de tentar serializar:

``` python
notify_ticket_created.delay(ticket)
```

A task pode recuperar os dados necessários no worker.

------------------------------------------------------------------------

# Retry

Um dos objetivos do projeto será experimentar os mecanismos de retry do
Celery.

Por exemplo:

``` text
Task
 │
 ├── sucesso → DONE
 │
 └── erro
      │
      ▼
    retry
      │
      ▼
   tentativa 2
      │
      ├── sucesso
      │
      └── erro
           │
           ▼
        tentativa 3
```

Isso será especialmente útil para operações externas como:

-   notificações;
-   processamento de arquivos;
-   chamadas para APIs;
-   geração de relatórios.

------------------------------------------------------------------------

# Idempotência

Tasks importantes deverão ser projetadas pensando em idempotência.

Por exemplo:

``` text
TicketCreated
```

não deve resultar em duas notificações se a mesma task for processada
novamente de maneira inesperada.

A arquitetura deverá considerar:

``` text
retry
duplicate message
worker restart
network failure
timeout
```

Esse será um dos pontos importantes para estudar com Celery.

------------------------------------------------------------------------

# Transaction Boundaries

As operações de banco deverão possuir limites transacionais claros.

Exemplo:

``` text
CreateTicket
    │
    ├── BEGIN
    │
    ├── INSERT ticket
    ├── INSERT relations
    ├── COMMIT
    │
    └── enqueue event/task
```

Um dos temas a ser estudado durante o projeto será a diferença entre:

``` text
database transaction
```

e:

``` text
message/task publication
```

especialmente para evitar situações onde o banco confirma uma operação
mas a mensagem não é publicada.

------------------------------------------------------------------------

# Possível evolução: Outbox Pattern

Caso seja necessário aprofundar o estudo de eventos, o projeto poderá
experimentar o **Transactional Outbox Pattern**.

Fluxo:

``` text
Application
     │
     ▼
BEGIN TRANSACTION
     │
     ├── Save Ticket
     │
     └── Save Event in Outbox
     │
     ▼
COMMIT
     │
     ▼
Outbox Worker
     │
     ▼
RabbitMQ
```

Isso permite estudar como manter consistência entre banco de dados e
mensageria.

A implementação do Outbox não é obrigatória na primeira versão.

------------------------------------------------------------------------

# CQRS leve

O projeto não pretende implementar CQRS completo.

A ideia é apenas separar semanticamente:

``` text
Commands → alteram estado
Queries  → consultam estado
```

Exemplo:

``` text
commands/
├── create_ticket.py
├── assign_ticket.py
└── close_ticket.py

queries/
├── get_ticket.py
└── list_tickets.py
```

A separação é principalmente semântica e organizacional. O projeto não
pretende implementar CQRS completo nem impor uma classe por operação.

------------------------------------------------------------------------

# Controller

O controller será responsável principalmente pela camada HTTP.

Exemplo conceitual:

``` python
@router.post("/tickets")
async def create_ticket(
    request: CreateTicketRequest,
    use_case: CreateTicket = Depends(...),
):
    return await use_case.execute(
        CreateTicketCommand(...)
    )
```

O controller não deve conter regra de negócio significativa.

Sua responsabilidade será:

``` text
HTTP
 ↓
Validation
 ↓
Application
 ↓
Response
```

------------------------------------------------------------------------

# Pydantic

Pydantic será utilizado na camada de apresentação para:

-   validar requests;
-   serializar responses;
-   validar parâmetros;
-   representar DTOs.

Exemplo:

``` python
class CreateTicketRequest(BaseModel):
    title: str
    description: str
    priority: TicketPriority
```

O domínio não precisa depender diretamente desses schemas HTTP.

------------------------------------------------------------------------

# Fluxo arquitetural

Para uma operação HTTP:

``` text
HTTP
 │
 ▼
Controller
 │
 ▼
Pydantic DTO
 │
 ▼
Application Use Case
 │
 ├───────────────┐
 ▼               ▼
Domain        Repository
                 │
                 ▼
             PostgreSQL
 │
 ▼
Domain Event
 │
 ▼
Message Broker
 │
 ▼
Celery Worker
 │
 ├── Redis
 ├── PostgreSQL
 ├── MinIO
 └── WebSocket
```

------------------------------------------------------------------------

# Regra de dependências

Uma regra importante do projeto:

``` text
Presentation
      ↓
Application
      ↓
Domain
```

e:

``` text
Infrastructure
      ↓
implements abstractions
```

O objetivo é evitar:

``` text
Domain
  ↓
SQLAlchemy
  ↓
FastAPI
  ↓
Redis
```

O domínio deve permanecer independente.

------------------------------------------------------------------------

# Modular Monolith vs Microservices

Este projeto **não será dividido em microserviços**.

Mesmo possuindo módulos:

``` text
auth
users
tickets
notifications
attachments
```

todos continuam dentro da mesma aplicação.

A ideia é aprender primeiro a criar bons limites internos.

Posteriormente, caso um módulo precise ser extraído para um serviço
separado, a separação existente facilita esse processo.

Exemplo:

``` text
Modular Monolith

┌───────────────────────────────┐
│           Backend             │
│                               │
│ Auth │ Users │ Tickets │ ...  │
└───────────────────────────────┘
```

Poderia eventualmente evoluir para:

``` text
┌──────────┐   ┌──────────┐
│  Auth    │   │ Tickets  │
└──────────┘   └──────────┘
       │            │
       └── Messages ┘
```

Mas essa evolução não faz parte do objetivo inicial.

------------------------------------------------------------------------

# Docker Compose

O ambiente local deverá possuir aproximadamente:

``` text
services:

  api
  worker
  postgres
  rabbitmq
  redis
  minio
```

Conceitualmente:

``` text
                    ┌──────────┐
                    │   API    │
                    └────┬─────┘
                         │
       ┌─────────────────┼─────────────────┐
       ▼                 ▼                 ▼
  PostgreSQL          Redis            RabbitMQ
                                           │
                                           ▼
                                      Celery Worker
                                           │
                                           ▼
                                         MinIO
```

O número de workers poderá ser aumentado para testar processamento
concorrente.

------------------------------------------------------------------------

# Observabilidade

Como o objetivo é estudar processamento assíncrono, será importante
observar:

-   duração das tasks;
-   quantidade de retries;
-   erros;
-   filas;
-   tasks pendentes;
-   workers ativos;
-   utilização de Redis;
-   conexões do PostgreSQL;
-   processamento de arquivos.

Uma futura evolução poderá incluir:

``` text
Prometheus
Grafana
Flower
OpenTelemetry
```

Essas ferramentas não são obrigatórias na primeira versão.

------------------------------------------------------------------------

# Funcionalidades iniciais

## Autenticação

-   [ ] Login
-   [ ] Logout
-   [ ] Sessões
-   [ ] Revogação de sessão
-   [ ] Proteção das rotas

## Usuários

-   [ ] Criar usuário
-   [ ] Listar usuários
-   [ ] Consultar usuário
-   [ ] Atualizar usuário
-   [ ] Desativar usuário

## Tickets

-   [ ] Criar ticket
-   [ ] Listar tickets
-   [ ] Consultar ticket
-   [ ] Atualizar ticket
-   [ ] Atribuir usuário
-   [ ] Adicionar watcher
-   [ ] Alterar status
-   [ ] Alterar prioridade
-   [ ] Fechar ticket
-   [ ] Reabrir ticket

## Comentários

-   [ ] Criar comentário
-   [ ] Listar comentários
-   [ ] Editar comentário
-   [ ] Remover comentário

## Attachments

-   [ ] Upload
-   [ ] Listagem
-   [ ] Download
-   [ ] Remoção
-   [ ] Metadata no PostgreSQL
-   [ ] Arquivo no MinIO

## Notificações

-   [ ] Ticket criado
-   [ ] Ticket atribuído
-   [ ] Novo comentário
-   [ ] Ticket resolvido
-   [ ] Ticket fechado

## Celery

-   [ ] Task simples
-   [ ] Retry
-   [ ] Exponential backoff
-   [ ] Task periódica
-   [ ] Task com prioridade
-   [ ] Geração de relatório
-   [ ] Processamento de attachments
-   [ ] Notificações assíncronas

## WebSocket

-   [ ] Conexão autenticada
-   [ ] Atualização de ticket
-   [ ] Novo comentário
-   [ ] Notificação em tempo real

------------------------------------------------------------------------

# Roadmap

## Fase 1 --- Base

-   [ ] Criar projeto
-   [ ] Configurar FastAPI
-   [ ] Configurar Pydantic Settings
-   [ ] Configurar PostgreSQL
-   [ ] Configurar SQLAlchemy
-   [ ] Configurar Alembic
-   [ ] Criar Docker Compose
-   [ ] Criar estrutura modular

## Fase 2 --- Auth e Users

-   [ ] User
-   [ ] UserSession
-   [ ] Login
-   [ ] Logout
-   [ ] Middleware/dependency de autenticação

## Fase 3 --- Tickets

-   [ ] Ticket
-   [ ] TicketUser
-   [ ] TicketComment
-   [ ] Status history
-   [ ] Commands
-   [ ] Queries
-   [ ] Repositories

## Fase 4 --- Redis

-   [ ] Client
-   [ ] Cache
-   [ ] Session storage
-   [ ] Locks
-   [ ] Rate limiting

## Fase 5 --- RabbitMQ + Celery

-   [ ] Configurar RabbitMQ
-   [ ] Configurar Celery
-   [ ] Criar worker
-   [ ] Criar primeira task
-   [ ] Retry
-   [ ] Backoff
-   [ ] Result backend
-   [ ] Task periódica
-   [ ] Concorrência

## Fase 6 --- MinIO

-   [ ] Configurar MinIO
-   [ ] Bucket
-   [ ] Upload
-   [ ] Download
-   [ ] Delete
-   [ ] Attachment metadata
-   [ ] Processamento assíncrono

## Fase 7 --- Eventos

-   [ ] Domain events
-   [ ] Event publisher
-   [ ] TicketCreated
-   [ ] TicketAssigned
-   [ ] TicketStatusChanged
-   [ ] TicketCommentAdded
-   [ ] Integração com Celery

## Fase 8 --- WebSockets

-   [ ] WebSocket Manager
-   [ ] Redis Pub/Sub
-   [ ] Atualizações de tickets
-   [ ] Notificações

## Fase 9 --- Relatórios

-   [ ] Criar job
-   [ ] Processar com Celery
-   [ ] Gerar PDF
-   [ ] Salvar no MinIO
-   [ ] Consultar status
-   [ ] Download do relatório

## Fase 10 --- Arquitetura avançada

-   [ ] Idempotência
-   [ ] Outbox Pattern
-   [ ] Dead Letter Queue
-   [ ] Observabilidade
-   [ ] Métricas
-   [ ] Tracing

------------------------------------------------------------------------

# Princípios do projeto

## 1. Domínio não conhece infraestrutura

Evitar:

``` python
from sqlalchemy import ...
from fastapi import ...
from celery import ...
```

dentro do domínio.

------------------------------------------------------------------------

## 2. Controller fino

Controllers devem ser responsáveis principalmente por:

``` text
HTTP → DTO → Use Case → Response
```

------------------------------------------------------------------------

## 3. Use Cases explícitos

Preferir:

``` text
CreateTicket
AssignTicket
CloseTicket
```

a:

``` text
TicketService
```

com dezenas de métodos.

------------------------------------------------------------------------

## 4. Tasks independentes de HTTP

Uma task deve poder ser disparada por:

``` text
HTTP
Scheduler
Outro worker
Evento
CLI
```

sem depender de `BackgroundTasks`.

------------------------------------------------------------------------

## 5. Infraestrutura como detalhe

Tecnologias podem mudar:

``` text
MinIO → S3
RabbitMQ → outro broker
PostgreSQL → outro banco
Redis → outro cache
```

sem exigir alterações nas regras centrais do domínio.

------------------------------------------------------------------------

## 6. Não abstrair por abstrair

Nem toda classe precisa de:

``` text
Interface
AbstractFactory
Repository
Service
Adapter
Provider
```

As abstrações devem existir quando houver uma razão arquitetural clara.

------------------------------------------------------------------------

# Objetivo final

Ao final, o sistema deverá representar uma aplicação backend
relativamente realista:

``` text
                         ┌───────────────┐
                         │    Client     │
                         └───────┬───────┘
                                 │
                                 ▼
                         ┌───────────────┐
                         │    FastAPI    │
                         └───────┬───────┘
                                 │
                  ┌──────────────┼──────────────┐
                  │              │              │
                  ▼              ▼              ▼
                Auth           Users          Tickets
                  │              │              │
                  └──────────────┼──────────────┘
                                 │
                                 ▼
                           PostgreSQL
                                 │
                         Domain Events
                                 │
                                 ▼
                            RabbitMQ
                                 │
                                 ▼
                         Celery Workers
                         │      │      │
                         ▼      ▼      ▼
                       Redis  MinIO  WebSocket
```

O principal objetivo não é criar a maior quantidade possível de
tecnologias, mas **entender claramente o papel de cada uma**.

O projeto deve servir como laboratório para responder perguntas como:

-   Quando usar processamento assíncrono?
-   Quando usar Celery em vez de `BackgroundTasks`?
-   Quando uma tarefa deve ir para uma fila?
-   Quando usar RabbitMQ e quando usar Redis?
-   Como lidar com retries?
-   Como tornar uma task idempotente?
-   Como separar domínio de infraestrutura?
-   Como organizar um projeto grande por módulos?
-   Quando usar Repository?
-   Quando uma Query merece uma implementação própria?
-   Como publicar eventos?
-   Como lidar com consistência entre banco e mensageria?
-   Como processar arquivos de forma assíncrona?
-   Como comunicar eventos em tempo real com WebSockets?

O projeto deve priorizar **aprendizado arquitetural e prático**,
mantendo a aplicação como um Modular Monolith simples de executar,
testar e evoluir.
