### 💻 Teste Técnico – Agrupamento de Pedidos

Você recebe uma lista de pedidos de um e-commerce.
Cada pedido possui as seguintes propriedades:

* `id`
* `customer`
* `product`
* `category`
* `price`

Exemplo de entrada:

```javascript
const orders = [
  { id: 1, customer: "Ana", product: "Camisa", category: "Roupas", price: 50 },
  { id: 2, customer: "João", product: "Calça", category: "Roupas", price: 120 },
  { id: 3, customer: "Ana", product: "Tênis", category: "Calçados", price: 200 },
  { id: 4, customer: "Maria", product: "Sandália", category: "Calçados", price: 80 },
  { id: 5, customer: "João", product: "Boné", category: "Acessórios", price: 40 },
];
```

### Desafio

Implemente uma função que **agrupa os pedidos por categoria** e retorne, para cada categoria:

* quantidade total de pedidos
* soma total dos preços
* ticket médio da categoria

### Regras

* Utilize **JavaScript puro**
* Não utilize bibliotecas externas
* A solução deve utilizar **`Array.reduce`**
* O resultado deve ser um **objeto agrupado por categoria**