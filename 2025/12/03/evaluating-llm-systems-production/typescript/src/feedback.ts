/**
 * Feedback capture module.
 * Handles explicit feedback and implicit signals.
 */

export interface ExplicitFeedback {
  request_id: string;
  thumbs_up?: boolean;
  rating?: number; // 1-5 scale
  labels?: Record<string, string>;
  timestamp: string;
}

export interface ImplicitSignal {
  request_id: string;
  signal_type: 'edit' | 'abandon' | 'repeat_query' | 'click_through' | 'time_spent';
  value?: number;
  metadata?: Record<string, any>;
  timestamp: string;
}

export class FeedbackCollector {
  private explicitFeedback: ExplicitFeedback[] = [];
  private implicitSignals: ImplicitSignal[] = [];
  private feedbackFile?: string;

  constructor(feedbackFile?: string) {
    this.feedbackFile = feedbackFile;
  }

  recordThumbsUp(request_id: string, thumbs_up: boolean): ExplicitFeedback {
    const feedback: ExplicitFeedback = {
      request_id,
      thumbs_up,
      timestamp: new Date().toISOString(),
    };
    this.explicitFeedback.push(feedback);
    this.saveFeedback(feedback);
    return feedback;
  }

  recordRating(request_id: string, rating: number): ExplicitFeedback {
    if (rating < 1 || rating > 5) {
      throw new Error('Rating must be between 1 and 5');
    }
    const feedback: ExplicitFeedback = {
      request_id,
      rating,
      timestamp: new Date().toISOString(),
    };
    this.explicitFeedback.push(feedback);
    this.saveFeedback(feedback);
    return feedback;
  }

  recordLabels(
    request_id: string,
    labels: Record<string, string>
  ): ExplicitFeedback {
    const feedback: ExplicitFeedback = {
      request_id,
      labels,
      timestamp: new Date().toISOString(),
    };
    this.explicitFeedback.push(feedback);
    this.saveFeedback(feedback);
    return feedback;
  }

  recordImplicitSignal(
    request_id: string,
    signal_type: ImplicitSignal['signal_type'],
    value?: number,
    metadata?: Record<string, any>
  ): ImplicitSignal {
    const signal: ImplicitSignal = {
      request_id,
      signal_type,
      value,
      metadata: metadata || {},
      timestamp: new Date().toISOString(),
    };
    this.implicitSignals.push(signal);
    this.saveSignal(signal);
    return signal;
  }

  recordEdit(request_id: string, editRatio: number): ImplicitSignal {
    return this.recordImplicitSignal(request_id, 'edit', editRatio, {
      high_edit: editRatio > 0.5,
    });
  }

  recordAbandon(request_id: string): ImplicitSignal {
    return this.recordImplicitSignal(request_id, 'abandon');
  }

  recordRepeatQuery(
    request_id: string,
    originalRequestId: string
  ): ImplicitSignal {
    return this.recordImplicitSignal(request_id, 'repeat_query', undefined, {
      original_request_id: originalRequestId,
    });
  }

  recordTimeSpent(request_id: string, seconds: number): ImplicitSignal {
    return this.recordImplicitSignal(request_id, 'time_spent', seconds);
  }

  getFeedbackStats(request_ids?: string[]): {
    total: number;
    thumbs_up_count: number;
    thumbs_down_count: number;
    avg_rating: number | null;
    label_counts: Record<string, Record<string, number>>;
  } {
    let feedbacks = this.explicitFeedback;
    if (request_ids) {
      feedbacks = feedbacks.filter((f) => request_ids.includes(f.request_id));
    }

    const stats = {
      total: feedbacks.length,
      thumbs_up_count: feedbacks.filter((f) => f.thumbs_up === true).length,
      thumbs_down_count: feedbacks.filter((f) => f.thumbs_up === false).length,
      avg_rating: null as number | null,
      label_counts: {} as Record<string, Record<string, number>>,
    };

    const ratings = feedbacks
      .map((f) => f.rating)
      .filter((r): r is number => r !== undefined);
    if (ratings.length > 0) {
      stats.avg_rating = ratings.reduce((a, b) => a + b, 0) / ratings.length;
    }

    // Count labels
    for (const feedback of feedbacks) {
      if (feedback.labels) {
        for (const [key, value] of Object.entries(feedback.labels)) {
          if (!stats.label_counts[key]) {
            stats.label_counts[key] = {};
          }
          stats.label_counts[key][value] =
            (stats.label_counts[key][value] || 0) + 1;
        }
      }
    }

    return stats;
  }

  private saveFeedback(feedback: ExplicitFeedback): void {
    if (this.feedbackFile && typeof require !== 'undefined') {
      const fs = require('fs');
      fs.appendFileSync(
        this.feedbackFile,
        JSON.stringify({
          type: 'explicit',
          ...feedback,
        }) + '\n'
      );
    }
  }

  private saveSignal(signal: ImplicitSignal): void {
    if (this.feedbackFile && typeof require !== 'undefined') {
      const fs = require('fs');
      fs.appendFileSync(
        this.feedbackFile,
        JSON.stringify({
          type: 'implicit',
          ...signal,
        }) + '\n'
      );
    }
  }
}

