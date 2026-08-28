-- CampusHire.AI row-level security
-- Run this in the Supabase SQL editor (or via the CLI) so the public anon key
-- cannot read or write another user's resumes, even if someone uses the JS client
-- directly. The FastAPI backend uses the service role and still verifies JWTs.

ALTER TABLE IF EXISTS public.resumes ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "resumes_select_own" ON public.resumes;
CREATE POLICY "resumes_select_own"
ON public.resumes
FOR SELECT
TO authenticated
USING (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "resumes_insert_own" ON public.resumes;
CREATE POLICY "resumes_insert_own"
ON public.resumes
FOR INSERT
TO authenticated
WITH CHECK (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "resumes_update_own" ON public.resumes;
CREATE POLICY "resumes_update_own"
ON public.resumes
FOR UPDATE
TO authenticated
USING (auth.uid()::text = user_id::text)
WITH CHECK (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "resumes_delete_own" ON public.resumes;
CREATE POLICY "resumes_delete_own"
ON public.resumes
FOR DELETE
TO authenticated
USING (auth.uid()::text = user_id::text);

REVOKE ALL ON TABLE public.resumes FROM anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.resumes TO authenticated;

-- Storage: users may only touch objects under their own uid prefix.
DROP POLICY IF EXISTS "resumes_storage_select_own" ON storage.objects;
CREATE POLICY "resumes_storage_select_own"
ON storage.objects
FOR SELECT
TO authenticated
USING (
  bucket_id = 'resumes'
  AND (storage.foldername(name))[1] = auth.uid()::text
);

DROP POLICY IF EXISTS "resumes_storage_insert_own" ON storage.objects;
CREATE POLICY "resumes_storage_insert_own"
ON storage.objects
FOR INSERT
TO authenticated
WITH CHECK (
  bucket_id = 'resumes'
  AND (storage.foldername(name))[1] = auth.uid()::text
);

DROP POLICY IF EXISTS "resumes_storage_update_own" ON storage.objects;
CREATE POLICY "resumes_storage_update_own"
ON storage.objects
FOR UPDATE
TO authenticated
USING (
  bucket_id = 'resumes'
  AND (storage.foldername(name))[1] = auth.uid()::text
)
WITH CHECK (
  bucket_id = 'resumes'
  AND (storage.foldername(name))[1] = auth.uid()::text
);

DROP POLICY IF EXISTS "resumes_storage_delete_own" ON storage.objects;
CREATE POLICY "resumes_storage_delete_own"
ON storage.objects
FOR DELETE
TO authenticated
USING (
  bucket_id = 'resumes'
  AND (storage.foldername(name))[1] = auth.uid()::text
);
