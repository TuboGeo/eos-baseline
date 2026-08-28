"""Performance evaluation metrics for scheduling algorithms."""


def compute_metrics(scheduled, rejected, runtime_ms, rejection_reasons=None,
                     satellite=None):
    total_requests = len(scheduled) + len(rejected)
    total_priority = sum(req.priority for req in scheduled)
    total_possible_priority = sum(req.priority for req in (scheduled + rejected))

    metrics = {
        'total_priority': total_priority,
        'total_possible_priority': total_possible_priority,
        'priority_achieved_ratio': (total_priority / total_possible_priority
                                     if total_possible_priority > 0 else 0),
        'scheduled_count': len(scheduled),
        'rejected_count': len(rejected),
        'completion_rate': len(scheduled) / total_requests if total_requests > 0 else 0,
        'runtime_ms': runtime_ms,
    }

    if rejection_reasons:
        reason_counts = {}
        for reason in rejection_reasons:
            if reason != "SCHEDULED":
                reason_counts[reason] = reason_counts.get(reason, 0) + 1
        metrics['rejection_breakdown'] = reason_counts

    if satellite is not None:
        energy_used = sum(r.energy for r in scheduled)
        storage_used = sum(r.data for r in scheduled)
        metrics['energy_used_pct'] = 100.0 * energy_used / satellite.energy_cap
        metrics['storage_used_pct'] = 100.0 * storage_used / satellite.storage_cap

    return metrics


def compare_algorithms(results):
    comparison = {}
    names = list(results.keys())
    if len(names) >= 2:
        baseline = names[0]
        for name in names[1:]:
            if results[baseline]['total_priority'] > 0:
                improvement = ((results[name]['total_priority'] - results[baseline]['total_priority'])
                               / results[baseline]['total_priority'] * 100)
            else:
                improvement = 0.0
            comparison[f"{name}_vs_{baseline}_improvement_pct"] = improvement
    return comparison
