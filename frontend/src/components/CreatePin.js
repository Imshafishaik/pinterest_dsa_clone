import React, { useState } from 'react';
import styled from 'styled-components';
import { useData } from '../context/DataContext';

const CreatePinContainer = styled.div`
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
`;

const CreatePinForm = styled.form`
  display: flex;
  flex-direction: column;
  gap: 15px;
`;

const FormGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: 5px;
`;

const Label = styled.label`
  font-weight: 600;
  color: #333;
`;

const Input = styled.input`
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
`;

const TextArea = styled.textarea`
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  min-height: 80px;
  resize: vertical;
`;

const Button = styled.button`
  padding: 12px 24px;
  background: #e60023;
  color: white;
  border: none;
  border-radius: 24px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    background: #d50821;
    transform: translateY(-1px);
  }

  &:disabled {
    background: #ccc;
    cursor: not-allowed;
    transform: none;
  }
`;

const Title = styled.h2`
  color: #333;
  margin-bottom: 20px;
`;

const CreatePin = () => {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    image_url: '',
    link: '',
    category: 'general',
    tags: [],
    author: 'Alice'
  });
  const [tagInput, setTagInput] = useState('');
  const { createPin, loading } = useData();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleTagAdd = (e) => {
    if (e.key === 'Enter' && tagInput.trim()) {
      e.preventDefault();
      setFormData(prev => ({
        ...prev,
        tags: [...prev.tags, tagInput.trim()]
      }));
      setTagInput('');
    }
  };

  const handleTagRemove = (tagToRemove) => {
    setFormData(prev => ({
      ...prev,
      tags: prev.tags.filter(tag => tag !== tagToRemove)
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      await createPin(formData);
      alert('Pin created successfully!');
      setFormData({
        title: '',
        description: '',
        image_url: '',
        link: '',
        category: 'general',
        tags: [],
        author: 'Alice'
      });
      setTagInput('');
    } catch (error) {
      alert('Error creating pin: ' + error.message);
    }
  };

  return (
    <CreatePinContainer>
      <Title>Create Pin</Title>
      <CreatePinForm onSubmit={handleSubmit}>
        <FormGroup>
          <Label htmlFor="title">Title *</Label>
          <Input
            type="text"
            id="title"
            name="title"
            value={formData.title}
            onChange={handleChange}
            required
            placeholder="Enter pin title"
          />
        </FormGroup>

        <FormGroup>
          <Label htmlFor="image_url">Image URL *</Label>
          <Input
            type="url"
            id="image_url"
            name="image_url"
            value={formData.image_url}
            onChange={handleChange}
            required
            placeholder="https://example.com/image.jpg"
          />
        </FormGroup>

        <FormGroup>
          <Label htmlFor="description">Description</Label>
          <TextArea
            id="description"
            name="description"
            value={formData.description}
            onChange={handleChange}
            placeholder="Describe your pin..."
          />
        </FormGroup>

        <FormGroup>
          <Label htmlFor="link">Link (optional)</Label>
          <Input
            type="url"
            id="link"
            name="link"
            value={formData.link}
            onChange={handleChange}
            placeholder="https://example.com"
          />
        </FormGroup>

        <FormGroup>
          <Label htmlFor="category">Category</Label>
          <Input
            type="text"
            id="category"
            name="category"
            value={formData.category}
            onChange={handleChange}
            placeholder="e.g., diy, food, travel"
          />
        </FormGroup>

        <FormGroup>
          <Label htmlFor="tags">Tags</Label>
          <Input
            type="text"
            id="tags"
            value={tagInput}
            onChange={(e) => setTagInput(e.target.value)}
            onKeyPress={handleTagAdd}
            placeholder="Press Enter to add tags"
          />
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px', marginTop: '5px' }}>
            {formData.tags.map((tag, index) => (
              <span
                key={index}
                style={{
                  background: '#e0e0e0',
                  padding: '4px 8px',
                  borderRadius: '12px',
                  fontSize: '12px',
                  cursor: 'pointer'
                }}
                onClick={() => handleTagRemove(tag)}
              >
                {tag} ×
              </span>
            ))}
          </div>
        </FormGroup>

        <Button type="submit" disabled={loading}>
          {loading ? 'Creating...' : 'Create Pin'}
        </Button>
      </CreatePinForm>
    </CreatePinContainer>
  );
};

export default CreatePin;
