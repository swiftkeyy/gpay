-- Create ENUM types for P2P marketplace
-- Run this if migration didn't create them

-- Check if types exist and create if not
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'seller_status_enum') THEN
        CREATE TYPE seller_status_enum AS ENUM ('pending', 'active', 'suspended', 'banned');
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'lot_delivery_type_enum') THEN
        CREATE TYPE lot_delivery_type_enum AS ENUM ('manual', 'auto', 'instant');
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'lot_status_enum') THEN
        CREATE TYPE lot_status_enum AS ENUM ('draft', 'active', 'out_of_stock', 'suspended', 'deleted');
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'deal_status_enum') THEN
        CREATE TYPE deal_status_enum AS ENUM ('created', 'paid', 'in_progress', 'waiting_confirmation', 'completed', 'disputed', 'canceled', 'refunded');
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'dispute_status_enum') THEN
        CREATE TYPE dispute_status_enum AS ENUM ('open', 'investigating', 'resolved', 'closed');
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'transaction_type_enum') THEN
        CREATE TYPE transaction_type_enum AS ENUM ('deposit', 'withdrawal', 'purchase', 'refund', 'commission', 'payout', 'bonus', 'penalty');
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'transaction_status_enum') THEN
        CREATE TYPE transaction_status_enum AS ENUM ('pending', 'completed', 'failed', 'canceled');
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'withdrawal_status_enum') THEN
        CREATE TYPE withdrawal_status_enum AS ENUM ('pending', 'processing', 'completed', 'failed', 'canceled');
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'notification_type_enum') THEN
        CREATE TYPE notification_type_enum AS ENUM ('order', 'deal', 'payment', 'review', 'system', 'promo');
    END IF;
END $$;
