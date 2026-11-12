import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseKey = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY;

if (!supabaseKey || !supabaseUrl) {
    throw new Error("Missing supabase vars");
}

//initiates connection to supabase, and lets u import same client everywhere in frontend
export const supabase = createClient(supabaseUrl, supabaseKey);

