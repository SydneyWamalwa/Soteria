import random

def assign_reviewers(eco_action, reviewer_pool, num_reviewers=3):
    """Assign random reviewers to a newly submitted eco-action."""
    selected_reviewers = random.sample(reviewer_pool, num_reviewers)
    for reviewer in selected_reviewers:
        review = EcoActionReview(
            eco_action_id=eco_action.id,
            reviewer_id=reviewer.id
        )
        db.session.add(review)
    db.session.commit()


def process_reviews(eco_action):
    """After all reviewers vote, finalize action status."""
    reviews = EcoActionReview.query.filter_by(eco_action_id=eco_action.id).all()
    decisions = [r.decision for r in reviews if r.decision]

    if len(decisions) < 3:
        return  # Wait for all votes

    approve_count = decisions.count('Approve')
    reject_count = decisions.count('Reject')

    if approve_count > reject_count:
        eco_action.status = 'Approved'
        eco_action.user.planet_credits += eco_action.points
    elif reject_count > approve_count:
        eco_action.status = 'Rejected'
    else:
        eco_action.status = 'Pending Moderator Review'

    db.session.commit()