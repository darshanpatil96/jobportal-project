/**
 * TypeScript types matching Django DRF serializers.
 * Keep in sync with api/serializers.py
 */

export interface Job {
  id: number;
  title: string;
  company: string;
  company_name: string;
  location: string;
  salary: string | null;
  category: string;
  job_type: 'Full-Time' | 'Part-Time' | 'Internship' | 'Remote';
  status: 'Open' | 'Closed' | 'Draft';
  posted_at: string;
  app_count?: number;
}

export interface JobDetail extends Job {
  description: string;
  required_skills: string[];
}

export interface Application {
  id: number;
  job: number;
  job_title: string;
  job_company: string;
  status: ApplicationStatus;
  applied_at: string;
  match_score: number | null;
}

export type ApplicationStatus =
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
  category_scores: Record<string, number>;
  skill_details: Record<string, number>;
  missing_skills: string[];
  computed_at: string;
}

export interface TimelineEvent {
  event_type: string;
  message: string;
  metadata: Record<string, unknown>;
  created_at: string;
}
