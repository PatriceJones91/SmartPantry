-- Phase 12: allow tracking of complete and near-complete recommendation groups.
alter table public.sp2_recommendation_results
    drop constraint if exists sp2_recommendation_results_candidate_group_check;

alter table public.sp2_recommendation_results
    add constraint sp2_recommendation_results_candidate_group_check
    check (candidate_group in (
        'expiry_led_complete',
        'other_complete',
        'expiry_led_near_complete',
        'other_near_complete'
    ));
