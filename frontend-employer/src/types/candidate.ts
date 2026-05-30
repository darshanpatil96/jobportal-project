/**
 * TypeScript types for the Employer ATS — candidate/pipeline domain.
 * Matches Django DRF serializers in api/employer/views.py
 */

export interface CandidateApplication {
  id: number;
  job: number;
  job_title: string;
  job_company: string;
  status: PipelineStatus;
  applied_at: string;
  match_score: number | null;
}

export interface CandidateDetail extends CandidateApplication {
  candidate: {
    username: string;
    email: string;
    phone: string;
    qualification: string;
    experience: string;
    cover_letter: string;
  };
  match_score_detail: MatchScore | null;
  parsed_resume: ParsedResume | null;
  allowed_statuses: PipelineStatus[];
  interviews: Interview[];
}

export type PipelineStatus =
  | 'Applied'
  | 'Screening'
  | 'Technical Round'
  | 'HR Round'
  | 'Final Review'
  | 'Offer Sent'
  | 'Hired'
  | 'Rejected'
  | 'Withdrawn';

export interface MatchScore {
  overall_score: number;
  category_scores: {
    skills: number;
    education: number;
    experience: number;
    semantic: number;
    keywords: number;
  };
  skill_details: Record<string, number>;
  missing_skills: string[];
  computed_at: string;
}

export interface ParsedResume {
  parse_status: 'pending' | 'success' | 'failed' | 'skipped';
  parsed_data: {
    skills: string[];
    education: string[];
    experience: string[];
    projects: string[];
    certifications: string[];
    email: string;
    phone: string;
    linkedin: string;
    github: string;
  };
  error_message: string;
  source_file: string;
  updated_at: string;
}

export interface Interview {
  id: number;
  application: number;
  candidate_name: string;
  job_title: string;
  scheduled_time: string;
  interview_type: 'Online' | 'Offline' | 'Technical' | 'HR' | 'Screening';
  meeting_link: string;
  notes: string;
  status: 'Scheduled' | 'Completed' | 'Cancelled' | 'Rescheduled';
  created_at: string;
}

export interface DashboardStats {
  total_jobs: number;
  total_applications: number;
  open_jobs: number;
  scheduled_interviews: number;
}

export interface PipelineCount {
  status: PipelineStatus;
  total: number;
}

export interface AnalyticsData {
  stats: DashboardStats;
  pipeline_counts: PipelineCount[];
  applications_per_job: Array<{ job__id: number; job__title: string; total: number }>;
  applications_per_category: Array<{ job__category: string; total: number }>;
}
