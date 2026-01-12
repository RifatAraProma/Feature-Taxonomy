import React from 'react';
import { getPlotUrl } from '../config/cdn';

export default function EvaluationPipeline() {
  return (
    <div style={{ 
      padding: '2rem', 
      maxWidth: '1400px', 
      margin: '0 auto',
      fontFamily: 'system-ui, -apple-system, sans-serif'
    }}>
      {/* Header */}
      <div style={{ marginBottom: '3rem', textAlign: 'center' }}>
        <h1 style={{ fontSize: '2.5rem', marginBottom: '1rem', color: '#1a1a1a' }}>
          ⚙️ Evaluation Pipeline: From Simplification to Grading
        </h1>
        <p style={{ fontSize: '1.2rem', color: '#666', lineHeight: '1.6' }}>
          Follow the complete 9-step grading methodology through an example: evaluating how well 
          <strong> Gaussian Filter</strong> preserves the <strong>Level (L¹ norm)</strong> feature when simplifying 
          <strong> Apple Stock (AAPL)</strong> price data across 100 smoothing levels.
        </p>
      </div>

      {/* Step 1: Data Comparison */}
      <Section title="Step 1: Original vs Simplified Output" stepNumber={1}>
        <p style={styles.text}>
          We have the Apple stock price dataset and we apply a <strong>Gaussian filter at level 50</strong>. 
        </p>
        
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem', marginTop: '1.5rem' }}>
          <ImageCard 
            title="Original Apple Stock Price (Level 0)"
            src={getPlotUrl('/plots/original/stock_aapl_price.svg')}
            alt="Original AAPL stock price"
          />
          <ImageCard 
            title="Gaussian Filter on the dataset at simplification degree 50"
            src={getPlotUrl('/plots/pipeline/gaussian_50.svg')}
            alt="Gaussian smoothed AAPL with transparent original overlay"
          />
        </div>

        <div style={styles.insight}>
        We generate 100 such simplification degrees (1-100) for each simplification technique. 
        </div>
      </Section>

      {/* Step 2: Feature Computation */}
      <Section title="Step 2: Computing Feature Similarity Metrics" stepNumber={2}>
        <p style={styles.text}>
          For each simplification degree, we compute <strong>21 feature preservation metrics</strong> in total, comparing 
          the simplified output to the original. These metrics measure how well specific visual characteristics are maintained.
        </p>

        <div style={{ marginTop: '1.5rem', marginBottom: '1.5rem' }}>
          <ImageCard 
            title="Level Feature Comparison: Original vs Smoothed"
            src={getPlotUrl('/plots/pipeline/level_overlay.svg')}
            alt="Level feature overlay showing point-wise differences"
            fullWidth
          />
        </div>

        <p style={styles.text}>
          For example, to compute <strong>Level similarity</strong> (point-wise L¹ norm), we calculate the absolute 
          difference between corresponding points in the original and simplified series. The highlighted regions in the 
          figure above show where these differences occur.
        </p>

        <div style={styles.insight}>
          <strong>💡 Key Point:</strong> Each metric produces a measurement of the error indicating how well 
          the simplified series preserves that specific visual feature. Lower error = better preservation.
        </div>
      </Section>

      {/* Step 3: Raw Scatter Plot */}
      <Section title="Step 3: Feature Similarity vs Pixel Approximate Entropy (PAE)" stepNumber={3}>
        <p style={styles.text}>
          Let's focus on one metric: <strong>L¹ norm</strong> for Level similarity. For all 100 levels 
          across all algorithms, we plot L¹ norm against Pixel Approximate Entropy. Higher PAE means less 
          simplification and therefore, less error or lower L¹ norm.
        </p>

        <div style={{ display: 'flex', justifyContent: 'center', marginTop: '1.5rem', marginBottom: '1rem' }}>
          <img 
            src={getPlotUrl('/plots/pipeline/algo_legend_horizontal.svg')}
            alt="Algorithm color legend"
            style={{ maxWidth: '100%', height: 'auto' }}
          />
        </div>

        <div style={{ marginTop: '1.5rem' }}>
          <ImageCard 
            title="Level L1: Raw Scatter (PAE vs Feature Similarity)"
            src={getPlotUrl('/plots/stock_aapl_price/ranking/level_l1_raw.svg')}
            alt="Raw scatter plot showing PAE vs level_l1 similarity"
            fullWidth
          />
        </div>

        <div style={styles.insight}>
          <strong>💡 Key Point:</strong> Each point represents one smoothing level from one algorithm. 
          The cloud of points shows the tradeoff: lower PAE (less perceptible change) but also potentially 
          lower feature preservation.
        </div>
      </Section>

      {/* Step 4: Z-Normalized Scatter */}
      <Section title="Step 4: Z-Score Normalization" stepNumber={4}>
        <p style={styles.text}>
          Raw error metrics have different scales across datasets, making them difficult to compare directly. 
          We normalize all metrics using <strong>z-scores</strong>: subtract the mean and divide by standard 
          deviation. This creates a unified scale where 0 = average error, but since these are error metrics, 
          <strong> positive z-scores mean worse than average error</strong>.
        </p>

        <div style={{ 
          marginTop: '1rem',
          marginBottom: '1.5rem',
          padding: '1rem', 
          backgroundColor: '#e3f2fd',
          borderRadius: '4px',
          border: '1px solid #2196F3'
        }}>
          <div style={{ marginBottom: '0.75rem' }}>
            <strong style={{ color: '#1976D2' }}>Converting Error to Preservation:</strong>
          </div>
          <div style={{ fontFamily: 'monospace', fontSize: '1rem', marginBottom: '0.5rem' }}>
            preservation_z = -error_z
          </div>
          <div style={{ fontSize: '0.9rem', color: '#666' }}>
            We negate the error z-score to flip the scale: now positive values indicate better-than-average preservation, 
            and negative values indicate worse-than-average preservation.
          </div>
        </div>

        <p style={styles.text}>
          Next, we compute the <strong>FC (Feature Complexity) score</strong> by subtracting the Pixel Approximate Entropy z-score from 
          the preservation z-score. PAE z-score indicates visual complexity or the simplification degree of the output.
          This gives us a score indicating feature preservation efficiency relative to 
          complexity or simplification degree: <strong>FC_score = preservation_z - pae_z</strong>.
        </p>

        <div style={{ display: 'flex', justifyContent: 'center', marginTop: '1.5rem', marginBottom: '1rem' }}>
          <img 
            src={getPlotUrl('/plots/pipeline/algo_legend_horizontal.svg')}
            alt="Algorithm color legend"
            style={{ maxWidth: '100%', height: 'auto' }}
          />
        </div>

        <div style={{ marginTop: '1.5rem' }}>
          <ImageCard 
            title="Level L1: Z-Normalized Scatter"
            src={getPlotUrl('/plots/stock_aapl_price/ranking/level_l1_zscore_fc.svg')}
            alt="Z-normalized scatter plot"
            fullWidth
          />
        </div>
      </Section>

      {/* Step 5: FC Score Quartile Categorization and Rating Distribution */}
      <Section title="Step 5: FC Score Categorization and Rating Distribution" stepNumber={5}>
        <p style={styles.text}>
          Now we categorize the <strong>FC scores</strong> into quartile-based rating buckets. 
          We compute the quartiles (Q1, Q2, Q3) of all FC scores across all simplification techniques and degrees and assign a
        rating based on where its FC score falls:
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginTop: '1.5rem' }}>
          <RatingCard 
            label="Excellent (E)"
            range="Top 25%"
            zscore="FC > Q3"
            color="#F0F0F0"
            textColor="#000"
            points={4}
          />
          <RatingCard 
            label="Good (G)"
            range="50-75%"
            zscore="Q2 < FC ≤ Q3"
            color="#CCCCCC"
            textColor="#000"
            points={3}
          />
          <RatingCard 
            label="Fair (F)"
            range="25-50%"
            zscore="Q1 < FC ≤ Q2"
            color="#999999"
            textColor="#000"
            points={2}
          />
          <RatingCard 
            label="Poor (P)"
            range="Bottom 25%"
            zscore="FC ≤ Q1"
            color="#666666"
            textColor="#000"
            points={1}
          />
        </div>

        <p style={styles.text}>
          Here's how the 100 simplification degrees are distributed across rating buckets for each simplification technique on Apple stock:
        </p>

        <div style={{ display: 'flex', justifyContent: 'center', marginTop: '1.5rem', marginBottom: '1rem' }}>
          <img 
            src={getPlotUrl('/plots/pipeline/algo_legend_horizontal.svg')}
            alt="Algorithm color legend"
            style={{ maxWidth: '100%', height: 'auto' }}
          />
        </div>

        <div style={{ marginTop: '1.5rem' }}>
          <ImageCard 
            title="Level L1: Rating Distribution per Algorithm"
            src={getPlotUrl('/plots/stock_aapl_price/ranking/level_l1_fc_distribution.svg')}
            alt="Distribution of ratings across algorithms"
            fullWidth
          />
        </div>

        <div style={styles.insight}>
          <strong>💡 Key Point:</strong> Each of the 100 simplification degrees gets assigned one of these 4 ratings 
          based on where its <strong>FC score</strong> falls in the quartile distribution. Different simplification techniques 
          produce different rating distributions — an ideal technique would have many degrees rated "Excellent" or "Good".
        </div>
      </Section>

      {/* Step 6: Grade Calculation */}
      <Section title="Step 6: Calculating the Grade (Single Dataset)" stepNumber={6}>
        <p style={styles.text}>
          For each algorithm on this dataset, we compute a <strong>weighted average score</strong> using 
          the rating counts from all 100 smoothing levels:
        </p>

        <div style={{ 
          marginTop: '1.5rem',
          padding: '1.5rem',
          backgroundColor: '#f5f5f5',
          borderRadius: '8px',
          border: '1px solid #ddd'
        }}>
          <div style={{ fontSize: '1.1rem', marginBottom: '1rem', textAlign: 'center' }}>
            <strong>Score Formula:</strong>
          </div>
          <div style={{ 
            fontSize: '1.3rem', 
            textAlign: 'center', 
            fontFamily: 'monospace',
            padding: '1rem',
            backgroundColor: 'white',
            borderRadius: '4px',
            margin: '1rem 0'
          }}>
            Score = (E×4 + G×3 + F×2 + P×1) / 100
          </div>
          <p style={{ fontSize: '0.95rem', color: '#666', textAlign: 'center', margin: '1rem 0 0 0' }}>
            where E, G, F, P are the counts of Excellent, Good, Fair, and Poor ratings across the 100 smoothing levels
          </p>
        </div>

        <ExampleCalculation />

        <div style={{ marginTop: '1.5rem' }}>
          <h4 style={{ marginBottom: '0.5rem', color: '#7B1FA2' }}>Letter Grade Assignment:</h4>
          <GradeThresholds />
        </div>
      </Section>

      {/* Step 7: Cross-Dataset Aggregation */}
      <Section title="Step 7: Aggregating Across All 80 Datasets" stepNumber={7}>
        <p style={styles.text}>
          So far, we've seen how to grade a single simplification technique and feature preservation metric pair on a single dataset.
          To get an idea about how well an algorithm preserves a feature, we need an aggregated grade across datasets.
        </p>

        <h3 style={{ fontSize: '1.3rem', marginTop: '2rem', marginBottom: '1rem', color: '#7B1FA2' }}>
          The Aggregation Process Across Datasets
        </h3>

        <div style={{ 
          marginTop: '1.5rem',
          padding: '1.5rem',
          backgroundColor: '#f3e5f5',
          borderRadius: '8px',
          border: '2px solid #9C27B0'
        }}>
          <h4 style={{ marginTop: 0, color: '#7B1FA2' }}>Example: Gaussian Filter + Level L¹</h4>
          <ol style={{ paddingLeft: '1.5rem', lineHeight: '1.8' }}>
            <li><strong>Repeat Steps 1-6 for all 80 datasets</strong>
              <ul style={{ marginTop: '0.5rem', color: '#666' }}>
                <li>astro_115_120 → Grade A</li>
                <li>chi_homicide_monthly → Grade A</li>
                <li>climate_atl_prcp → Grade A</li>
                <li>climate_atl_tmax → Grade A</li>
                <li>...and 76 more datasets</li>
              </ul>
            </li>
            <li style={{ marginTop: '1rem' }}><strong>Collect all 80 letter grades</strong>
              <div style={{ 
                marginTop: '0.5rem',
                padding: '0.75rem',
                backgroundColor: 'white',
                borderRadius: '4px',
                fontFamily: 'monospace',
                fontSize: '0.95rem'
              }}>
                [A, A, A, A, A, A, A, A, A, A, A, A, A, A, A, A, ...]
              </div>
              <div style={{ marginTop: '0.5rem', color: '#666', fontSize: '0.9rem' }}>
                Final distribution: 80 A's
              </div>
            </li>
            <li style={{ marginTop: '1rem' }}><strong>Find the most common grade (mode)</strong>
              <div style={{ marginTop: '0.5rem', color: '#666' }}>
                Count how many times each grade appears:
              </div>
              <div style={{ 
                marginTop: '0.5rem',
                padding: '0.75rem',
                backgroundColor: 'white',
                borderRadius: '4px',
                fontFamily: 'monospace',
                fontSize: '0.95rem'
              }}>
                A: 80 datasets<br/>
                B: 0 datasets<br/>
                C: 0 datasets<br/>
                D: 0 datasets<br/>
                F: 0 datasets
              </div>
            </li>
            <li style={{ marginTop: '1rem' }}><strong>Select the grade with highest count</strong>
              <div style={{ marginTop: '0.5rem', color: '#666' }}>
                Grade A appears 80 times (most frequent) → <strong>Mode = A</strong>
              </div>
              <div style={{ marginTop: '0.5rem', color: '#666', fontSize: '0.9rem', fontStyle: 'italic' }}>
                Note: If multiple grades have the same highest count (a tie), we highlight all common grades as the mode.
              </div>
            </li>
          </ol>
        </div>

        <h3 style={{ fontSize: '1.3rem', marginTop: '2.5rem', marginBottom: '1rem', color: '#7B1FA2' }}>
          The Complete Algorithm × Metric Performance Matrix
        </h3>

        <p style={styles.text}>
          Following the same aggregation process for <strong>all 19 algorithms × 21 metrics</strong> (399 combinations), 
          we get a comprehensive heatmap showing which algorithms excel at preserving which visual features:
        </p>

        <div style={{ marginTop: '2rem', marginBottom: '2rem' }}>
          <ImageCard 
            title="Algorithm × Metric Mode Grades Heatmap"
            src={getPlotUrl('/plots/fc_visualizations/algorithm_metric_mode_grades.svg')}
            alt="Heatmap showing mode grades for all algorithm-metric combinations"
            fullWidth
          />
        </div>

        <div style={{ 
          marginTop: '1.5rem',
          padding: '1.5rem',
          backgroundColor: '#f3e5f5',
          borderRadius: '8px',
          border: '2px solid #9C27B0'
        }}>
          <h4 style={{ marginTop: 0, color: '#7B1FA2' }}>Key Insight</h4>
          <p style={{ margin: 0, color: '#666' }}>
            Each cell represents 80 datasets worth of evaluation. For example, the "Gaussian Filter + Level L¹" cell
            shows Grade A (appears 80 out of 80 times) — the most common outcome we just calculated. This matrix reveals algorithm strengths and weaknesses 
            across different visual features based on typical performance.
          </p>
        </div>
      </Section>

      {/* Step 8: Deviation Calculation */}
      <Section title="Step 8: Measuring Consistency with Mode and Deviation" stepNumber={8}>
        <p style={styles.text}>
          The mode grade tells us the most common outcome, but it doesn't reveal consistency. An algorithm might get 
          50 A's and 30 F's (mode=A, but inconsistent) or 75 A's and 5 B's (mode=A, very consistent) — both have 
          the same mode, but behave very differently in practice.
        </p>

        <p style={styles.text}>
          We calculate <strong>deviation</strong> to quantify this spread. Deviation measures what percentage of datasets 
          received grades different from the most common grade:
        </p>

        <div style={{ 
          marginTop: '1.5rem',
          padding: '1.5rem',
          backgroundColor: '#fff3e0',
          borderRadius: '8px',
          border: '2px solid #FF9800'
        }}>
          <div style={{ fontSize: '1.1rem', marginBottom: '1rem', textAlign: 'center' }}>
            <strong>Deviation Formula:</strong>
          </div>
          <div style={{ 
            fontSize: '1.3rem', 
            textAlign: 'center', 
            fontFamily: 'monospace',
            padding: '1rem',
            backgroundColor: 'white',
            borderRadius: '4px',
            margin: '1rem 0'
          }}>
            Deviation = ((n - mode_count) / n) × 100%
          </div>
          <p style={{ fontSize: '0.95rem', color: '#666', textAlign: 'center', margin: '0.5rem 0 0 0' }}>
            where n = total datasets (80), mode_count = number of datasets with the most common grade
          </p>
        </div>

        <div style={{ 
          marginTop: '2rem',
          padding: '1.5rem',
          backgroundColor: 'white',
          borderRadius: '8px',
          border: '2px solid #9C27B0'
        }}>
          <h4 style={{ marginTop: 0, color: '#7B1FA2' }}>Step-by-Step Deviation Calculation Example</h4>
          
          <p style={{ fontSize: '1rem', margin: '1rem 0' }}>
            Suppose Gaussian Filter + level_l1 gets these grades across 80 datasets:
          </p>
          
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: '1fr 1fr', 
            gap: '2rem', 
            marginTop: '1rem' 
          }}>
            <div>
              <p style={{ fontWeight: 'bold', marginBottom: '0.5rem', color: '#4CAF50' }}>
                Scenario 1: Consistent Performance
              </p>
              <div style={{ 
                fontFamily: 'monospace', 
                fontSize: '0.9rem', 
                backgroundColor: '#f5f5f5',
                padding: '1rem',
                borderRadius: '4px',
                marginBottom: '0.5rem'
              }}>
                74× A<br/>
                6× B<br/>
                0× C, 0× D, 0× F<br/><br/>
                <strong>Step 1:</strong> Find mode<br/>
                &nbsp;&nbsp;Mode = A (appears 74 times)<br/>
                <strong>Step 2:</strong> Calculate deviation:<br/>
                &nbsp;&nbsp;Deviation = ((80 - 74) / 80) × 100%<br/>
                &nbsp;&nbsp;Deviation = (6 / 80) × 100%<br/>
                &nbsp;&nbsp;Deviation = <strong style={{ color: '#4CAF50' }}>7.5%</strong> ✓ Very low deviation
              </div>
              <p style={{ fontSize: '0.9rem', color: '#666', margin: 0 }}>
                <strong>Interpretation:</strong> 92.5% of datasets get the mode grade (A). Highly predictable and reliable behavior.
              </p>
            </div>

            <div>
              <p style={{ fontWeight: 'bold', marginBottom: '0.5rem', color: '#FF5722' }}>
                Scenario 2: Variable Performance
              </p>
              <div style={{ 
                fontFamily: 'monospace', 
                fontSize: '0.9rem', 
                backgroundColor: '#f5f5f5',
                padding: '1rem',
                borderRadius: '4px',
                marginBottom: '0.5rem'
              }}>
                30× A<br/>
                15× B<br/>
                15× C<br/>
                15× D<br/>
                5× F<br/>
                <strong>Step 1:</strong> Find mode<br/>
                &nbsp;&nbsp;Mode = A (appears 30 times)<br/>
                <strong>Step 2:</strong> Calculate deviation:<br/>
                &nbsp;&nbsp;Deviation = ((80 - 30) / 80) × 100%<br/>
                &nbsp;&nbsp;Deviation = (50 / 80) × 100%<br/>
                &nbsp;&nbsp;Deviation = <strong style={{ color: '#FF5722' }}>62.5%</strong> ✗ High deviation
              </div>
              <p style={{ fontSize: '0.9rem', color: '#666', margin: 0 }}>
                <strong>Interpretation:</strong> Only 37.5% of datasets get the mode grade. Highly variable — works well on some data, poorly on others.
              </p>
            </div>
          </div>
        </div>

        <h3 style={{ fontSize: '1.3rem', marginTop: '2.5rem', marginBottom: '1rem', color: '#1976D2' }}>
          The Complete Deviation Table
        </h3>

        <p style={styles.text}>
          For all 399 algorithm-metric combinations, we compute deviation alongside mode grades. The table uses 
          three color thresholds to indicate consistency:
        </p>

        <div style={{ 
          marginTop: '1.5rem',
          padding: '1.5rem',
          backgroundColor: '#fff3e0',
          borderRadius: '8px',
          border: '2px solid #FF9800',
          marginBottom: '1.5rem'
        }}>
          <h4 style={{ marginTop: 0, color: '#E65100', fontSize: '1.3rem' }}>Deviation Color Map</h4>
          <ul style={{ margin: '0.5rem 0', paddingLeft: '1.5rem', lineHeight: '1.8', fontSize: '1rem' }}>
            <li><strong style={{ color: '#ffcc66' }}>Light orange (&lt;25%):</strong> Highly predictable — more than 75% of datasets get the mode grade</li>
            <li><strong style={{ color: '#ff9900' }}>Medium orange (25-50%):</strong> Generally reliable — 50-75% of datasets get the mode grade</li>
            <li><strong style={{ color: '#e66600' }}>Dark orange (&gt;50%):</strong> Unpredictable — less than 50% of datasets get the mode grade</li>
          </ul>
          <p style={{ margin: '0.5rem 0 0 0', color: '#666', fontSize: '0.95rem' }}>
            <strong>Note:</strong> Deviation measures consistency, not quality. An algorithm can be consistently excellent (&lt;25% deviation, mode=A) 
            or consistently poor (&lt;25% deviation, mode=F). High deviation indicates variable behavior across different dataset types.
          </p>
        </div>

        <div style={{ marginTop: '2rem', marginBottom: '1.5rem' }}>
          <ImageCard 
            title="Algorithm × Metric Deviation Table"
            src={getPlotUrl('/plots/pipeline/deviation_table.svg')}
            alt="Deviation table showing consistency of each algorithm-metric combination"
            fullWidth
          />
        </div>
      </Section>

      {/* Summary Section */}
      <Section title="Visual Summary: Grade Distribution and Deviation" stepNumber={9}>
        <p style={{ fontSize: '1.1rem', lineHeight: '1.8', color: '#333', marginBottom: '1.5rem' }}>
          The histogram grid visualization combines both key evaluation metrics into a single comprehensive view, 
          showing how each algorithm-metric combination performs across all 80 datasets:
        </p>

        <div style={{
          backgroundColor: '#f5f5f5',
          padding: '1.5rem',
          borderRadius: '8px',
          marginBottom: '2rem',
          border: '1px solid #ddd'
        }}>
          <h4 style={{ marginTop: 0, color: '#7B1FA2', fontSize: '1.3rem', marginBottom: '1rem' }}>Understanding the Histogram Grid</h4>
          
          <div style={{ marginBottom: '1.5rem' }}>
            <p style={{ margin: '0.5rem 0', fontSize: '1rem', lineHeight: '1.8' }}>
              <strong style={{ color: '#7B1FA2' }}>Purple Histogram Bars (Grade Distribution):</strong> Show how many datasets 
              received each letter grade (A, B, C, D, F). The height of each bar represents the count of datasets. 
              The tallest bar indicates the <strong>mode grade</strong> — the most common outcome across all 80 datasets. 
              <em>In case of a tie (two grades with equal counts), we highlight both grades as co-modes.</em>
            </p>
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <p style={{ margin: '0.5rem 0', fontSize: '1rem', lineHeight: '1.8' }}>
              <strong style={{ color: '#E65100' }}>Orange Deviation Line (Consistency):</strong> The colored line below each histogram 
              indicates how consistent the performance is. The color directly corresponds to the deviation percentage:
            </p>
            <ul style={{ margin: '0.5rem 0', paddingLeft: '2rem', lineHeight: '1.8', fontSize: '1rem' }}>
              <li><strong>Light orange (&lt;25%):</strong> Most datasets agree on the same grade</li>
              <li><strong>Medium orange (25-50%):</strong> Moderate agreement with some variation</li>
              <li><strong>Dark orange (&gt;50%):</strong> High variation in grades across datasets</li>
            </ul>
          </div>

          <div>
            <p style={{ margin: '0.5rem 0', fontSize: '1rem', lineHeight: '1.8' }}>
              <strong style={{ color: '#333' }}>Example Interpretation:</strong> If you see a histogram with one tall purple bar (grade A) 
              and a light orange deviation line, it means the algorithm consistently earns A grades across most datasets — 
              high quality <em>and</em> high consistency. Conversely, a histogram with bars spread across multiple grades 
              and a dark orange line indicates unpredictable behavior.
            </p>
          </div>
        </div>

        <div style={{ marginTop: '2rem', marginBottom: '1.5rem' }}>
          <ImageCard 
            title="Algorithm × Metric Grade Distribution with Deviation Indicators"
            src={getPlotUrl('/plots/fc_visualizations/algorithm_metric_histogram_grid_mode.svg')}
            alt="Histogram grid showing grade distribution (purple bars) and deviation (orange lines) for each algorithm-metric combination"
            fullWidth
          />
        </div>

        <div style={styles.insight}>
          <strong>Summary:</strong> This histogram grid is the complete evaluation snapshot — it shows both 
          <em> what grade</em> algorithms typically receive (mode grade from tallest bar) and <em>how reliable</em> that 
          grade is across different datasets (deviation from orange line color). Together, these metrics help identify 
          algorithms that are both high-performing and consistently reliable across diverse time series types.
        </div>
      </Section>

    </div>
  );
}

// Helper Components

interface SectionProps {
  title: string;
  stepNumber: number;
  children: React.ReactNode;
}

function Section({ title, stepNumber, children }: SectionProps) {
  return (
    <section style={{ 
      marginBottom: '3rem',
      padding: '2rem',
      backgroundColor: 'white',
      borderRadius: '12px',
      boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
      border: '1px solid #e0e0e0'
    }}>
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        marginBottom: '1.5rem',
        paddingBottom: '1rem',
        borderBottom: '2px solid #9c27b0'
      }}>
        <div style={{ 
          width: '48px',
          height: '48px',
          borderRadius: '50%',
          backgroundColor: '#9c27b0',
          color: 'white',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '1.5rem',
          fontWeight: 'bold',
          marginRight: '1rem',
          flexShrink: 0
        }}>
          {stepNumber}
        </div>
        <h2 style={{ margin: 0, fontSize: '1.8rem', color: '#1a1a1a' }}>{title}</h2>
      </div>
      {children}
    </section>
  );
}

interface ImageCardProps {
  title: string;
  src: string;
  alt: string;
  fullWidth?: boolean;
}

function ImageCard({ title, src, alt, fullWidth }: ImageCardProps) {
  return (
    <div style={{ 
      border: '1px solid #ddd', 
      borderRadius: '8px', 
      overflow: 'hidden',
      backgroundColor: 'white',
      ...(fullWidth ? { gridColumn: '1 / -1' } : {})
    }}>
      <div style={{ 
        padding: '0.75rem 1rem', 
        backgroundColor: '#f5f5f5', 
        borderBottom: '1px solid #ddd',
        fontWeight: 'bold'
      }}>
        {title}
      </div>
      <div style={{ padding: '1rem', display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '300px' }}>
        <img src={src} alt={alt} style={{ maxWidth: '100%', height: 'auto' }} />
      </div>
    </div>
  );
}

interface FeatureCardProps {
  category: string;
  count: number;
  examples: string;
  color: string;
}

function FeatureCard({ category, count, examples, color }: FeatureCardProps) {
  return (
    <div style={{ 
      padding: '1.5rem', 
      border: `3px solid ${color}`,
      borderRadius: '8px',
      backgroundColor: 'white'
    }}>
      <div style={{ 
        fontSize: '1.3rem', 
        fontWeight: 'bold', 
        color, 
        marginBottom: '0.5rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <span>{category}</span>
        <span style={{ 
          backgroundColor: color, 
          color: 'white', 
          padding: '0.25rem 0.75rem', 
          borderRadius: '20px',
          fontSize: '0.9rem'
        }}>
          {count}
        </span>
      </div>
      <p style={{ margin: 0, color: '#666', fontSize: '0.9rem' }}>{examples}</p>
    </div>
  );
}

interface RatingCardProps {
  label: string;
  range: string;
  zscore: string;
  color: string;
  textColor?: string;
  points: number;
}

function RatingCard({ label, range, zscore, color, textColor = 'white', points }: RatingCardProps) {
  // Convert hex color to rgba with 0.25 opacity for background
  const hexToRgba = (hex: string) => {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, 0.25)`;
  };

  return (
    <div style={{ 
      padding: '1.5rem',
      backgroundColor: hexToRgba(color),
      color: textColor,
      borderRadius: '8px',
      textAlign: 'center',
      boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
      border: '1px solid rgba(0,0,0,0.1)'
    }}>
      <div style={{ fontSize: '1.4rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>
        {label}
      </div>
      <div style={{ fontSize: '0.95rem', marginBottom: '0.5rem' }}>
        {range}
      </div>
      <div style={{ fontSize: '0.85rem', fontFamily: 'monospace', marginBottom: '0.75rem' }}>
        {zscore}
      </div>
      <div style={{ 
        fontSize: '1.2rem', 
        fontWeight: 'bold',
        padding: '0.5rem',
        backgroundColor: 'rgba(0,0,0,0.1)',
        borderRadius: '4px'
      }}>
        {points} point{points !== 1 ? 's' : ''}
      </div>
    </div>
  );
}

function ExampleCalculation() {
  return (
    <div style={{ 
      marginTop: '1.5rem',
      padding: '1.5rem',
      backgroundColor: 'white',
      borderRadius: '8px',
      border: '2px solid #2196F3'
    }}>
      <h4 style={{ marginTop: 0, color: '#1976D2' }}>Example: Gaussian Filter on Apple Stock (level_l1)</h4>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem', marginTop: '1rem' }}>
        <div>
          <p style={{ fontWeight: 'bold', marginBottom: '0.5rem' }}>Rating Counts (101 levels):</p>
          <ul style={{ margin: 0, paddingLeft: '1.5rem', lineHeight: '1.8', fontFamily: 'monospace' }}>
            <li>Excellent: 99</li>
            <li>Good: 1</li>
            <li>Fair: 0</li>
            <li>Poor: 0</li>
          </ul>
        </div>
        <div>
          <p style={{ fontWeight: 'bold', marginBottom: '0.5rem' }}>Calculation:</p>
          <div style={{ fontFamily: 'monospace', fontSize: '0.95rem', lineHeight: '1.8' }}>
            Score = (99×4 + 1×3 + 0×2 + 0×1) / 101<br/>
            Score = (396 + 3 + 0 + 0) / 101<br/>
            Score = 399 / 100<br/>
            Score = <strong style={{ color: '#4a1a7a' }}>3.99</strong> → Grade: <strong style={{ color: '#4a1a7a' }}>A</strong>
          </div>
        </div>
      </div>
    </div>
  );
}

function GradeThresholds() {
  const thresholds = [
    { grade: 'A', range: '≥ 3.4', color: '#4a1a7a', textColor: '#fff' },
    { grade: 'B', range: '2.8 - 3.4', color: '#7340b8', textColor: '#fff' },
    { grade: 'C', range: '2.2 - 2.8', color: '#9b6fd9', textColor: '#fff' },
    { grade: 'D', range: '1.6 - 2.2', color: '#c9a8e8', textColor: '#000' },
    { grade: 'F', range: '< 1.6', color: '#e6d5f5', textColor: '#000' }
  ];

  return (
    <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
      {thresholds.map(({ grade, range, color, textColor }) => (
        <div key={grade} style={{ 
          flex: 1,
          padding: '0.75rem',
          backgroundColor: color,
          color: textColor,
          borderRadius: '4px',
          textAlign: 'center',
          border: '1px solid rgba(0,0,0,0.1)'
        }}>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>{grade}</div>
          <div style={{ fontSize: '0.85rem', opacity: 0.95 }}>{range}</div>
        </div>
      ))}
    </div>
  );
}

function VarianceExample() {
  return (
    <div style={{ 
      marginTop: '1.5rem',
      padding: '1.5rem',
      backgroundColor: 'white',
      borderRadius: '8px',
      border: '2px solid #9C27B0'
    }}>
      <h4 style={{ marginTop: 0, color: '#7B1FA2' }}>Example: Gaussian Filter + level_l1 across 80 datasets</h4>
      
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem', marginTop: '1rem' }}>
        <div>
          <p style={{ fontWeight: 'bold', marginBottom: '0.5rem', color: '#4CAF50' }}>
            Scenario 1: Low Variance (Consistent)
          </p>
          <div style={{ 
            fontFamily: 'monospace', 
            fontSize: '0.9rem', 
            backgroundColor: '#f5f5f5',
            padding: '1rem',
            borderRadius: '4px',
            marginBottom: '0.5rem'
          }}>
            45× A (4.0), 30× B (3.0), 5× C (2.0)<br/>
            Mean = 3.5, Variance = <strong style={{ color: '#4CAF50' }}>0.35</strong>
          </div>
          <p style={{ fontSize: '0.9rem', color: '#666', margin: 0 }}>
            Algorithm performs well on nearly all datasets. Predictable and reliable.
          </p>
        </div>

        <div>
          <p style={{ fontWeight: 'bold', marginBottom: '0.5rem', color: '#FF5722' }}>
            Scenario 2: High Variance (Inconsistent)
          </p>
          <div style={{ 
            fontFamily: 'monospace', 
            fontSize: '0.9rem', 
            backgroundColor: '#f5f5f5',
            padding: '1rem',
            borderRadius: '4px',
            marginBottom: '0.5rem'
          }}>
            25× A (4.0), 10× B (3.0), 15× C (2.0), 20× D (1.0), 10× F (0.0)<br/>
            Mean = 2.1, Variance = <strong style={{ color: '#FF5722' }}>1.79</strong>
          </div>
          <p style={{ fontSize: '0.9rem', color: '#666', margin: 0 }}>
            Algorithm is a "gamble" — works great sometimes, fails badly other times.
          </p>
        </div>
      </div>
    </div>
  );
}

const styles = {
  text: {
    fontSize: '1.05rem',
    lineHeight: '1.7',
    color: '#444',
    margin: '1rem 0'
  },
  insight: {
    marginTop: '1.5rem',
    padding: '1rem 1.5rem',
    backgroundColor: '#e8eaf6',
    borderLeft: '4px solid #3f51b5',
    borderRadius: '4px',
    fontSize: '1rem',
    lineHeight: '1.6'
  }
};
