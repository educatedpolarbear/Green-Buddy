'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/auth-context';
import Link from 'next/link';
import { ArrowLeft, Video, X, Save, Youtube } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Spinner } from '@/components/ui/spinner';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Material } from '@/types/learning';

interface Category {
  id: number;
  title: string;
  description: string;
  content_type?: string;
}

export default function EditVideoPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const { user } = useAuth();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [categories, setCategories] = useState<Category[]>([]);
  const [thumbnailUrl, setThumbnailUrl] = useState('');
  const [videoId, setVideoId] = useState('');
  const [videoPreview, setVideoPreview] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [material, setMaterial] = useState<Material | null>(null);
  const [formData, setFormData] = useState({
    title: '',
    content: '',
    category_id: '',
    excerpt: '',
    duration: '',
    type: 'video'
  });

  useEffect(() => {
    if (!user) {
      router.push('/auth/login');
      return;
    }
    
    const isAdmin = user.roles && user.roles.includes('admin');
    
    const fetchMaterial = async () => {
      try {
        const token = localStorage.getItem('token');
        const materialId = params.id;
        
        const response = await fetch(`/api/learning/materials/${materialId}`, {
          headers: {
            'Authorization': token ? `Bearer ${token}` : '',
          }
        });
        
        const data = await response.json();
        if (data.success && data) {
          const material = data;
          setMaterial(material);
          
          const isAuthor = material.author_id === user.id;
          
          if (!isAdmin && !isAuthor) {
            router.push('/learning');
            return;
          }
          
          setFormData({
            title: material.title,
            content: material.content,
            category_id: material.category_id.toString(),
            excerpt: material.excerpt || '',
            duration: material.duration || '',
            type: material.type
          });
          
          if (material.thumbnail_url) {
            setThumbnailUrl(material.thumbnail_url);
          }
          
          setVideoId(material.content);
          setVideoPreview(material.content);
        } else {
          setError(data.error || 'Failed to fetch material');
          setTimeout(() => router.push('/learning'), 3000);
        }
      } catch (error) {
        setError('Error fetching material');
        console.error(error);
        setTimeout(() => router.push('/learning'), 3000);
      }
    };

    const fetchCategories = async () => {
      try {
        const response = await fetch('/api/learning/categories');
        if (!response.ok) {
          throw new Error(`Error: ${response.status}`);
        }
        const data = await response.json();
        
        if (data.categories) {
          const videoCategories = data.categories.filter(
            (cat: Category) => cat.content_type === 'general' || cat.content_type === 'video'
          );
          setCategories(videoCategories);
        } else if (Array.isArray(data)) {
          setCategories(data);
        } else {
          setCategories([]);
        }
      } catch (error) {
        console.error('Error fetching categories:', error);
        setError('Failed to load categories. Please try again later.');
        setCategories([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchMaterial();
    fetchCategories();
  }, [user, router, params.id]);

  const extractYouTubeId = (url: string): string | null => {
    const regExp = /^.*(youtu.be\/|v\/|e\/|u\/\w+\/|embed\/|v=)([^#\&\?]*).*/;
    const match = url.match(regExp);
    return (match && match[2].length === 11) ? match[2] : null;
  };

  const handleVideoUrlChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const url = e.target.value;
    setVideoId(url);
    
    const youtubeId = extractYouTubeId(url);
    if (youtubeId) {
      setFormData({ ...formData, content: youtubeId });
      const thumbnailUrl = `https://img.youtube.com/vi/${youtubeId}/maxresdefault.jpg`;
      setThumbnailUrl(thumbnailUrl);
      setVideoPreview(youtubeId);
    } else if (url.match(/^[a-zA-Z0-9_-]{11}$/)) {
      setFormData({ ...formData, content: url });
      setThumbnailUrl(`https://img.youtube.com/vi/${url}/maxresdefault.jpg`);
      setVideoPreview(url);
    } else {
      setFormData({ ...formData, content: '' });
      setThumbnailUrl('');
      setVideoPreview(null);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.title.trim() || !formData.content.trim() || !formData.category_id) {
      setError('Please fill in all required fields.');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const excerpt = formData.excerpt.trim() || formData.title;
      
      const materialId = params.id;
      const response = await fetch(`/api/learning/materials/${materialId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          title: formData.title,
          content: formData.content,
          category_id: parseInt(formData.category_id),
          type: 'video',
          excerpt: excerpt,
          thumbnail_url: thumbnailUrl,
          duration: formData.duration
        })
      });

      if (response.ok) {
        const data = await response.json();
        router.push(`/learning/video/${materialId}`);
      } else {
        const errorData = await response.json();
        console.error('Error response:', errorData);
        setError(errorData.error || 'Failed to update video. Please try again.');
      }
    } catch (error) {
      console.error('Error updating video:', error);
      setError('An unexpected error occurred. Please try again later.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!material && !isLoading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <Alert variant="destructive" className="max-w-md">
          <AlertDescription>
            {error || 'Video not found. Redirecting...'}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#f8f9f3] py-12 relative">
      {/* Nature-themed background */}
      <div 
        className="absolute inset-0 bg-cover bg-center opacity-10 z-0" 
        style={{ 
          backgroundImage: "url('https://images.unsplash.com/photo-1501854140801-50d01698950b?ixlib=rb-1.2.1&auto=format&fit=crop&w=1950&q=80')",
          backgroundAttachment: "fixed"
        }}
        aria-hidden="true"
      />
      
      <div className="container mx-auto px-4 relative z-10">
        <div className="max-w-4xl mx-auto">
          <div className="mb-6">
            <Link
              href={`/learning/video/${params.id}`}
              className="inline-flex items-center text-[#2c5530] hover:text-[#3a6b3e] transition-colors"
            >
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Video
            </Link>
          </div>

          <Card className="border-[#d1e0d3] overflow-hidden bg-white shadow-md">
            <CardHeader className="bg-[#f0f4e9] border-b border-[#d1e0d3] pb-6">
              <div className="flex items-center mb-2">
                <Video className="mr-2 h-5 w-5 text-[#e76f51]" />
                <h1 className="text-2xl font-bold text-[#2c5530]">Edit Video</h1>
              </div>
              <p className="text-[#5a7d61]">Update video information.</p>
            </CardHeader>

            <CardContent className="p-6">
              <form onSubmit={handleSubmit} className="space-y-6">
                {error && (
                  <Alert variant="destructive">
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}

                <div className="space-y-2">
                  <Label htmlFor="title" className="text-[#2c5530] font-medium">
                    Title <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="title"
                    placeholder="Give your video a descriptive title"
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                    className="border-[#d1e0d3] focus-visible:ring-[#2c5530]"
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="category" className="text-[#2c5530] font-medium">
                    Category <span className="text-red-500">*</span>
                  </Label>
                  <Select
                    value={formData.category_id}
                    onValueChange={(value) => {
                      setFormData({ ...formData, category_id: value });
                    }}
                    required
                  >
                    <SelectTrigger className="border-[#d1e0d3] focus:ring-[#2c5530]">
                      <SelectValue placeholder="Select a category" />
                    </SelectTrigger>
                    <SelectContent>
                      {categories.map((category) => (
                        <SelectItem key={category.id} value={String(category.id)}>
                          {category.title}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="videoUrl" className="text-[#2c5530] font-medium">
                    YouTube Video URL or ID <span className="text-red-500">*</span>
                  </Label>
                  <div className="relative">
                    <Youtube className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                    <Input
                      id="videoUrl"
                      placeholder="Enter YouTube URL (e.g., https://www.youtube.com/watch?v=XXXXXXXX) or video ID"
                      value={videoId}
                      onChange={handleVideoUrlChange}
                      className="pl-10 border-[#d1e0d3] focus-visible:ring-[#2c5530]"
                      required
                    />
                  </div>
                  <p className="text-xs text-[#5a7d61]">
                    We currently support YouTube videos only.
                  </p>
                </div>

                {videoPreview && (
                  <div className="space-y-2">
                    <Label className="text-[#2c5530] font-medium">Video Preview</Label>
                    <div className="aspect-video bg-gray-100 relative rounded-md overflow-hidden">
                      <iframe
                        src={`https://www.youtube.com/embed/${videoPreview}`}
                        title="YouTube video player"
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                        allowFullScreen
                        className="absolute top-0 left-0 w-full h-full"
                      ></iframe>
                    </div>
                  </div>
                )}

                <div className="space-y-2">
                  <Label htmlFor="duration" className="text-[#2c5530] font-medium">
                    Duration
                  </Label>
                  <Input
                    id="duration"
                    placeholder="e.g., 12:45"
                    value={formData.duration}
                    onChange={(e) => setFormData({ ...formData, duration: e.target.value })}
                    className="border-[#d1e0d3] focus-visible:ring-[#2c5530]"
                  />
                  <p className="text-xs text-[#5a7d61]">
                    Format: MM:SS (e.g., 10:30 for 10 minutes and 30 seconds)
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="excerpt" className="text-[#2c5530] font-medium">
                    Description
                  </Label>
                  <Textarea
                    id="excerpt"
                    placeholder="A brief description of the video content"
                    value={formData.excerpt}
                    onChange={(e) => setFormData({ ...formData, excerpt: e.target.value })}
                    className="border-[#d1e0d3] focus-visible:ring-[#2c5530]"
                    rows={4}
                  />
                </div>

                <div className="pt-4 flex justify-end space-x-4">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => router.push(`/learning/video/${params.id}`)}
                    className="border-[#d1e0d3] text-[#2c5530] hover:bg-[#f0f4e9]"
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    disabled={isSubmitting}
                    className="bg-[#2c5530] hover:bg-[#3a6b3e] text-white"
                  >
                    {isSubmitting ? <Spinner size="sm" className="mr-2" /> : <Save className="mr-2 h-4 w-4" />}
                    Save Changes
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
} 