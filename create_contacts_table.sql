CREATE TABLE contacts (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    status TEXT DEFAULT 'new' CHECK (status IN ('new', 'read', 'replied')),
    user_id UUID REFERENCES auth.users(id)
);

-- Enable Row Level Security
ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Enable read access for authenticated users" ON contacts
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Enable insert for all users" ON contacts
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Enable update for authenticated users" ON contacts
    FOR UPDATE USING (auth.role() = 'authenticated'); 