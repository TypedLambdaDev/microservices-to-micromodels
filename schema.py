SCHEMA = {
    "user": {
        "table": "users",
        "fields": ["id", "name", "email", "age"]
    },
    
    "order": {
        "table": "orders",
        "fields": ["id", "user_id", "amount"]
    }
}