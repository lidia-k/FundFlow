import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Download, ArrowLeft, AlertCircle, CheckCircle2 } from 'lucide-react';
import { api } from '../api/client';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Button,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  Badge,
  Alert,
  AlertDescription,
  useToast,
} from '@/components/ui';

interface SALTResult {
  id: string;
  company_name: string;
  state: string;
  revenue: number;
  lp_name: string;
  ownership_percentage: number;
  salt_allocation: number;
  tax_amount: number;
}

interface CalculationResult {
  session_id: string;
  status: 'processing' | 'completed' | 'failed';
  results: SALTResult[];
  summary: {
    total_companies: number;
    total_revenue: number;
    total_salt_allocation: number;
    total_tax_amount: number;
  };
  created_at: string;
}

export default function ResultsShadcn() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [result, setResult] = useState<CalculationResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!sessionId) {
      setError('No session ID provided');
      setLoading(false);
      return;
    }

    const fetchResults = async () => {
      try {
        const data = await api.getCalculation(sessionId);
        setResult(data);
      } catch (err) {
        console.error('Error fetching results:', err);
        setError('Failed to load calculation results');
      } finally {
        setLoading(false);
      }
    };

    fetchResults();
  }, [sessionId]);

  const handleDownload = async () => {
    if (!sessionId) return;

    try {
      toast({
        title: "Downloading...",
        description: "Preparing your Excel file",
      });

      await api.downloadResults(sessionId);

      toast({
        title: "Download complete",
        description: "Your results have been downloaded",
      });
    } catch (error) {
      console.error('Download error:', error);
      toast({
        title: "Download failed",
        description: "Please try again later",
        variant: "destructive",
      });
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const formatPercentage = (value: number) => {
    return `${(value * 100).toFixed(2)}%`;
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto p-6">
        <div className="flex items-center justify-center min-h-96">
          <div className="text-center space-y-4">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto" />
            <p className="text-muted-foreground">Loading calculation results...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error || !result) {
    return (
      <div className="max-w-7xl mx-auto p-6">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            {error || 'Failed to load results'}
          </AlertDescription>
        </Alert>
        <div className="mt-6">
          <Button onClick={() => navigate('/upload')} variant="outline">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Upload
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-8 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold tracking-tight">SALT Calculation Results</h1>
          <p className="mt-2 text-muted-foreground">
            Session: {sessionId} • Processed on {new Date(result.created_at).toLocaleDateString()}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Badge
            variant={result.status === 'completed' ? 'default' : 'destructive'}
          >
            {result.status === 'completed' && <CheckCircle2 className="h-3 w-3 mr-1" />}
            {result.status.charAt(0).toUpperCase() + result.status.slice(1)}
          </Badge>
          <Button onClick={() => navigate('/upload')} variant="outline">
            <ArrowLeft className="h-4 w-4 mr-2" />
            New Upload
          </Button>
          <Button onClick={handleDownload}>
            <Download className="h-4 w-4 mr-2" />
            Download Excel
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Total Companies</CardDescription>
            <CardTitle className="text-2xl">{result.summary.total_companies}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Total Revenue</CardDescription>
            <CardTitle className="text-2xl">{formatCurrency(result.summary.total_revenue)}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>SALT Allocation</CardDescription>
            <CardTitle className="text-2xl">{formatCurrency(result.summary.total_salt_allocation)}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Total Tax Amount</CardDescription>
            <CardTitle className="text-2xl">{formatCurrency(result.summary.total_tax_amount)}</CardTitle>
          </CardHeader>
        </Card>
      </div>

      {/* Results Table */}
      <Card>
        <CardHeader>
          <CardTitle>Detailed Results</CardTitle>
          <CardDescription>
            SALT calculations for each portfolio company and LP
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Company</TableHead>
                  <TableHead>State</TableHead>
                  <TableHead>LP Name</TableHead>
                  <TableHead className="text-right">Revenue</TableHead>
                  <TableHead className="text-right">Ownership %</TableHead>
                  <TableHead className="text-right">SALT Allocation</TableHead>
                  <TableHead className="text-right">Tax Amount</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {result.results.map((row) => (
                  <TableRow key={row.id}>
                    <TableCell className="font-medium">{row.company_name}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{row.state}</Badge>
                    </TableCell>
                    <TableCell>{row.lp_name}</TableCell>
                    <TableCell className="text-right">{formatCurrency(row.revenue)}</TableCell>
                    <TableCell className="text-right">{formatPercentage(row.ownership_percentage)}</TableCell>
                    <TableCell className="text-right">{formatCurrency(row.salt_allocation)}</TableCell>
                    <TableCell className="text-right font-medium">{formatCurrency(row.tax_amount)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Status Alert */}
      {result.status === 'completed' && (
        <Alert>
          <CheckCircle2 className="h-4 w-4" />
          <AlertDescription>
            SALT calculations completed successfully. You can download the detailed Excel report above.
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}