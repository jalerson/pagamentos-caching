-- O status não é armazenado: a API o calcula usando created_at.
CREATE TABLE payments (
    id UUID PRIMARY KEY,
    card_token VARCHAR(84) NOT NULL,
    amount NUMERIC(12, 2) NOT NULL CHECK (amount > 0),
    currency CHAR(3) NOT NULL CHECK (currency = 'BRL'),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL
);
