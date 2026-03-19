import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

let supabaseClient = null;

function getSupabaseClient() {
  if (!supabaseUrl || !supabaseAnonKey) {
    throw new Error(
      'Supabase is not configured. Add VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY.'
    );
  }

  if (!supabaseClient) {
    supabaseClient = createClient(supabaseUrl, supabaseAnonKey);
  }

  return supabaseClient;
}

export async function fetchSavedTranslations() {
  const supabase = getSupabaseClient();
  const { data, error } = await supabase
    .from('saved_translations')
    .select(
      'id, source_text, translated_text, source_language, target_language, created_at'
    )
    .order('created_at', { ascending: false });

  if (error) {
    throw new Error('Could not load saved translations.');
  }

  return data ?? [];
}

export async function findSavedTranslation(sourceText, translatedText) {
  const supabase = getSupabaseClient();
  const { data, error } = await supabase
    .from('saved_translations')
    .select(
      'id, source_text, translated_text, source_language, target_language, created_at'
    )
    .eq('source_text', sourceText)
    .eq('translated_text', translatedText)
    .limit(1)
    .maybeSingle();

  if (error) {
    throw new Error('Could not check saved status.');
  }

  return data ?? null;
}

export async function checkTranslationSaved(sourceText, translatedText) {
  const match = await findSavedTranslation(sourceText, translatedText);
  return Boolean(match);
}

export async function saveTranslation({
  sourceText,
  translatedText,
  sourceLanguage,
  targetLanguage,
}) {
  const supabase = getSupabaseClient();
  const existingRecord = await findSavedTranslation(sourceText, translatedText);

  if (existingRecord) {
    return { status: 'duplicate', record: existingRecord };
  }

  const { data, error } = await supabase
    .from('saved_translations')
    .insert({
      source_text: sourceText,
      translated_text: translatedText,
      source_language: sourceLanguage,
      target_language: targetLanguage,
    })
    .select(
      'id, source_text, translated_text, source_language, target_language, created_at'
    )
    .single();

  if (error) {
    throw new Error('Could not save translation.');
  }

  return { status: 'saved', record: data };
}

export async function deleteSavedTranslation(sourceText, translatedText) {
  const supabase = getSupabaseClient();
  const existingRecord = await findSavedTranslation(sourceText, translatedText);

  if (!existingRecord) {
    return { status: 'missing' };
  }

  const { error } = await supabase
    .from('saved_translations')
    .delete()
    .eq('id', existingRecord.id);

  if (error) {
    throw new Error('Could not remove saved translation.');
  }

  return { status: 'removed' };
}
