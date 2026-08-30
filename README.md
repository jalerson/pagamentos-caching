# Pagamentos assíncronos com caching

API didática em FastAPI com exatamente 2 operações de negócio: criar uma solicitação de pagamento e consultar seu estado. O PostgreSQL guarda as solicitações; o Redis guarda temporariamente as respostas das consultas. Todo pagamento aparece como `processando` durante 30 segundos e depois como `aprovado`.

## Executar a API, o PostgreSQL e o Redis

Para executar os serviços, é necessário ter o Docker Desktop instalado.

```bash
docker compose up --build
```

Documentação: `http://127.0.0.1:8000/docs`

## Instalar o REST Client no Visual Studio Code

As requisições de exemplo estão no arquivo `requisicoes.http`. Para executá-las, instale a extensão [REST Client](https://marketplace.visualstudio.com/items?itemName=humao.rest-client), de Huachao Mao:

1. Abra a área **Extensions** do Visual Studio Code com `Cmd+Shift+X` no macOS ou `Ctrl+Shift+X` no Windows e Linux.
2. Pesquise por `REST Client` ou pelo identificador `humao.rest-client`.
3. Selecione a extensão **REST Client** e clique em **Install**.

Também é possível pressionar `F1`, procurar por `Extensions: Install Extensions` e pesquisar por `REST Client`.

## Executar as requisições

1. Inicie a API, o PostgreSQL e o Redis.
2. Abra `requisicoes.http` no Visual Studio Code.
3. Clique em **Send Request** acima da requisição desejada.
4. Execute primeiro **Solicitar pagamento**. O REST Client reutilizará automaticamente o identificador retornado nas consultas seguintes.
5. Respeite os intervalos indicados nos títulos das requisições para observar a expiração do TTL, uma resposta temporariamente desatualizada e a aprovação posterior.

A primeira consulta apresenta `X-Cache: MISS`; uma repetição dentro do TTL apresenta `X-Cache: HIT`. O TTL padrão é 15 segundos. Depois desse tempo, o Redis remove a chave e a consulta seguinte volta ao PostgreSQL.

Em um `HIT`, a API devolve exatamente a cópia armazenada. Por isso, ela pode continuar apresentando `processando` mesmo depois dos 30 segundos necessários para a aprovação. Somente quando o TTL expira, um novo `MISS` consulta o PostgreSQL, calcula o estado atual e preenche o cache novamente. Essa janela de possível desatualização é uma das desvantagens do caching: um TTL maior reduz consultas à fonte, mas pode manter dados antigos por mais tempo.

Para observar esse comportamento, faça a primeira consulta imediatamente, aguarde cerca de 20 segundos e consulte novamente para criar uma nova entrada ainda com `processando`. Depois dos 30 segundos contados desde a criação, consulte antes que essa segunda entrada expire: a resposta será um `HIT` ainda desatualizado. Após a expiração, a consulta seguinte será um `MISS` e apresentará `aprovado`.

Para acompanhar a expiração em tempo real, consulte no `redis-cli` o TTL da chave `pagamento:<id>`.

## Banco de dados

O PostgreSQL roda no serviço `database` do Docker Compose. O arquivo `database/001_schema.sql` cria a tabela `payments` na primeira inicialização do volume.

Reiniciar os contêineres preserva os pagamentos. Para recriar o banco vazio, remova o volume e inicie os serviços novamente:

```bash
docker compose down -v
docker compose up --build
```

## Executar os testes

Inicie primeiro o PostgreSQL:

```bash
docker compose up -d database
```

Depois, execute os testes:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
pytest
```

## Limites didáticos

Esta aplicação não processa um cartão nem executa trabalho em segundo plano. Ela deriva o status apenas quando recebe um `GET`. Uma implementação real normalmente exige integração com um provedor, fila, workers, idempotência, autenticação, HTTPS, observabilidade e tratamento de falhas.

O exemplo recebe somente um token fictício de cartão. Ele não armazena número de cartão nem código de segurança.
