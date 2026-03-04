-- ============================================
-- TABLA 1: garmin_connections
-- ============================================
CREATE TABLE public.garmin_connections (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL UNIQUE,
    garmin_email TEXT NOT NULL,
    garmin_password_encrypted TEXT NOT NULL,
    garmin_tokens TEXT,
    tokens_updated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE public.garmin_connections ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own garmin connection"
    ON public.garmin_connections FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own garmin connection"
    ON public.garmin_connections FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own garmin connection"
    ON public.garmin_connections FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own garmin connection"
    ON public.garmin_connections FOR DELETE
    USING (auth.uid() = user_id);

-- ============================================
-- TABLA 2: user_goals (metas personalizadas)
-- ============================================
CREATE TABLE public.user_goals (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL UNIQUE,
    steps_avg INTEGER DEFAULT 10000,
    activities INTEGER DEFAULT 28,
    strength INTEGER DEFAULT 10,
    sleep_75_days INTEGER DEFAULT 15,
    sleep_hours_avg NUMERIC(3,1) DEFAULT 7.5,
    hr_zone_1_3 NUMERIC(4,1) DEFAULT 19.3,
    hr_zone_4_5 NUMERIC(4,1) DEFAULT 2.9,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE public.user_goals ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own goals"
    ON public.user_goals FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own goals"
    ON public.user_goals FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own goals"
    ON public.user_goals FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own goals"
    ON public.user_goals FOR DELETE
    USING (auth.uid() = user_id);
