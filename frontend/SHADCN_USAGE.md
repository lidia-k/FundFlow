# Shadcn UI Components Usage Guide

This document explains how to use the Shadcn UI components that have been set up in the FundFlow frontend project.

## 🚀 Setup Complete

Shadcn UI has been successfully configured with the following components:

- **Button** - Various button styles and sizes
- **Card** - Container components with header, content, and footer
- **Progress** - Progress bars for loading states
- **Table** - Data tables with sorting and styling
- **Alert** - Alert messages for notifications
- **Toast** - Toast notifications
- **Input** - Form input fields
- **Badge** - Status indicators
- **FileUpload** - Custom drag-and-drop file upload component

## 📦 Dependencies Added

The following packages have been added to support Shadcn UI:

```json
{
  "@radix-ui/react-alert-dialog": "^1.0.5",
  "@radix-ui/react-dialog": "^1.0.5",
  "@radix-ui/react-dropdown-menu": "^2.0.6",
  "@radix-ui/react-progress": "^1.0.3",
  "@radix-ui/react-slot": "^1.0.2",
  "@radix-ui/react-toast": "^1.1.5",
  "class-variance-authority": "^0.7.0",
  "lucide-react": "^0.292.0",
  "tailwind-merge": "^2.0.0",
  "tailwindcss-animate": "^1.0.7"
}
```

## 🎨 Component Examples

### 1. Button Component

```tsx
import { Button } from '@/components/ui';

// Different variants
<Button variant="default">Primary Button</Button>
<Button variant="secondary">Secondary Button</Button>
<Button variant="outline">Outline Button</Button>
<Button variant="destructive">Delete Button</Button>
<Button variant="ghost">Ghost Button</Button>

// Different sizes
<Button size="sm">Small</Button>
<Button size="default">Default</Button>
<Button size="lg">Large</Button>

// With icons
<Button>
  <Upload className="h-4 w-4 mr-2" />
  Upload File
</Button>
```

### 2. Card Component

```tsx
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui';

<Card>
  <CardHeader>
    <CardTitle>Card Title</CardTitle>
    <CardDescription>Card description text</CardDescription>
  </CardHeader>
  <CardContent>
    <p>Main content goes here</p>
  </CardContent>
  <CardFooter>
    <Button>Action</Button>
  </CardFooter>
</Card>
```

### 3. Progress Component

```tsx
import { Progress } from '@/components/ui';

const [progress, setProgress] = useState(0);

<Progress value={progress} className="w-full" />
```

### 4. Table Component

```tsx
import { Table, TableHeader, TableBody, TableHead, TableRow, TableCell } from '@/components/ui';

<Table>
  <TableHeader>
    <TableRow>
      <TableHead>Name</TableHead>
      <TableHead>Status</TableHead>
      <TableHead className="text-right">Amount</TableHead>
    </TableRow>
  </TableHeader>
  <TableBody>
    <TableRow>
      <TableCell>Company A</TableCell>
      <TableCell>Active</TableCell>
      <TableCell className="text-right">$1,000</TableCell>
    </TableRow>
  </TableBody>
</Table>
```

### 5. Toast Notifications

```tsx
import { useToast } from '@/components/ui';

const { toast } = useToast();

// Success toast
toast({
  title: "Success!",
  description: "Your file has been uploaded successfully.",
});

// Error toast
toast({
  title: "Error",
  description: "Something went wrong.",
  variant: "destructive",
});
```

### 6. Alert Component

```tsx
import { Alert, AlertDescription } from '@/components/ui';
import { AlertCircle } from 'lucide-react';

<Alert>
  <AlertCircle className="h-4 w-4" />
  <AlertDescription>
    This is an informational alert message.
  </AlertDescription>
</Alert>

<Alert variant="destructive">
  <AlertCircle className="h-4 w-4" />
  <AlertDescription>
    This is an error alert message.
  </AlertDescription>
</Alert>
```

### 7. Badge Component

```tsx
import { Badge } from '@/components/ui';

<Badge>Default</Badge>
<Badge variant="secondary">Secondary</Badge>
<Badge variant="destructive">Error</Badge>
<Badge variant="outline">Outline</Badge>
```

### 8. Custom FileUpload Component

```tsx
import { FileUpload } from '@/components/ui';

const [file, setFile] = useState<File | null>(null);

<FileUpload
  onFileSelect={(file) => setFile(file)}
  onFileRemove={() => setFile(null)}
  selectedFile={file}
  accept={{
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
    "application/vnd.ms-excel": [".xls"],
  }}
  maxSize={10 * 1024 * 1024} // 10MB
  disabled={false}
/>
```

### 9. Input Component

```tsx
import { Input } from '@/components/ui';

<Input
  type="email"
  placeholder="Enter your email"
  value={email}
  onChange={(e) => setEmail(e.target.value)}
/>
```

## 🛠 Sample Pages

Two sample pages have been created to demonstrate the components:

1. **UploadShadcn.tsx** - Shows file upload with progress tracking
2. **ResultsShadcn.tsx** - Shows data table with results display

## 🎨 Theming

The components use CSS variables for theming. The color scheme can be customized in `/src/index.css`:

```css
:root {
  --primary: 221.2 83.2% 53.3%;
  --secondary: 210 40% 96%;
  --destructive: 0 84.2% 60.2%;
  /* ... other variables */
}
```

## 📱 Responsive Design

All components are responsive by default. Use Tailwind CSS classes for additional responsive behavior:

```tsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
  <Card>...</Card>
  <Card>...</Card>
</div>
```

## 🚨 Migration from Existing Components

To migrate from your existing components to Shadcn UI:

1. Replace `className="btn-primary"` with `<Button variant="default">`
2. Replace `className="card"` with `<Card>`
3. Use `useToast()` instead of `react-hot-toast`
4. Replace custom tables with the new `<Table>` component

## 📚 Additional Resources

- [Shadcn UI Documentation](https://ui.shadcn.com/)
- [Radix UI Primitives](https://www.radix-ui.com/primitives)
- [Tailwind CSS](https://tailwindcss.com/)
- [Lucide Icons](https://lucide.dev/)

## 🔧 Installation Command

To add more Shadcn UI components in the future, use:

```bash
npx shadcn-ui@latest add [component-name]
```

Note: Since we've manually set up the components, you may need to adjust the installation command to match your project structure.