def processar_order(orders):
    # Dicionários para agrupar dados por categoria
    category_counts = {}
    category_sums = {}
    
    # Totais globais
    quantidade_total_pedidos = len(orders)
    soma_total_precos = 0
    
    for order in orders:
        category = order['category']
        price = order['price']
        
        # Atualiza totais por categoria
        category_counts[category] = category_counts.get(category, 0) + 1
        category_sums[category] = category_sums.get(category, 0) + price
        
        # Atualiza total global de preços
        soma_total_precos += price
    
    # Calcula Ticket Médio por categoria
    # Nota: Conforme solicitado, o cálculo é (quantidade_de_pedidos / soma_dos_preços)
    #print(category_counts)
    #print(category_sums)
    
    ticket_medio_breakdown = {}
    for category in category_counts:
        count = category_counts[category] # 2
        total_price = category_sums[category] # 170
        
        # Evita divisão por zero se o total for 0
        if total_price != 0:
            ticket_medio_breakdown[f"{category}_tm"] = total_price / count
        else:
            ticket_medio_breakdown[f"{category}_tm"] = 0
            
    # Retorna o objeto final estruturado
    return {
        "quantidade_total_pedidos": quantidade_total_pedidos,
        "soma_total_precos": soma_total_precos,
        "ticket_medio": ticket_medio_breakdown
    }

def main():
    orders = [
        { "id": 1, "customer": "Ana", "product": "Camisa", "category": "Roupas", "price": 50 },
        { "id": 2, "customer": "João", "product": "Calça", "category": "Roupas", "price": 120 },
        { "id": 3, "customer": "Ana", "product": "Tênis", "category": "Calçados", "price": 200 },
        { "id": 4, "customer": "Maria", "product": "Sandália", "category": "Calçados", "price": 80 },
        { "id": 5, "customer": "João", "product": "Boné", "category": "Acessórios", "price": 40 },
    ]
    
    resultado = processar_order(orders)
    print(resultado)

if __name__ == "__main__":
    main()
