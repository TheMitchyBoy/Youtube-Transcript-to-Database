export interface SyncJob {
  id: number;
  name: string | null;
  channel_account: string;
  max_videos: number | null;
  languages: string[];
  frequency: string;
  enabled: boolean;
  force_refresh: boolean;
  include_videos: boolean;
  include_streams: boolean;
  include_live: boolean;
  last_run_at: string | null;
  next_run_at: string | null;
  last_status: string;
  last_error: string | null;
  created_at: string;
  updated_at: string;
}

export interface SyncRun {
  id: number;
  job_id: number;
  started_at: string;
  finished_at: string | null;
  status: string;
  videos_processed: number;
  transcripts_saved: number;
  transcripts_skipped: number;
  errors: number;
  message: string | null;
}

export interface FrequencyOption {
  value: string;
  label: string;
}

export interface ChannelSummary {
  id: number;
  youtube_channel_id: string;
  name: string | null;
  url: string;
  transcript_count: number;
}

export interface Stats {
  channels: number;
  videos: number;
  transcripts: number;
  sync_jobs: number;
}

export interface SyncJobInput {
  name?: string | null;
  channel_account: string;
  max_videos?: number | null;
  languages: string[];
  frequency: string;
  enabled: boolean;
  force_refresh: boolean;
  include_videos: boolean;
  include_streams: boolean;
  include_live: boolean;
}

export interface TranscriptSummary {
  id: number;
  video_id: number;
  youtube_video_id: string;
  video_title: string | null;
  video_url: string;
  content_type: string;
  is_live: boolean;
  channel_id: number;
  channel_name: string | null;
  language: string;
  language_code: string;
  is_auto_generated: boolean;
  preview: string;
  fetched_at: string;
}

export interface TranscriptDetail extends TranscriptSummary {
  content: string;
}
