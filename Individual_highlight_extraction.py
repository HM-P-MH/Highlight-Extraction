import fitz  # PyMuPDF
import statistics
import re
import openai

# Cleans and combines text extracted from word boundaries.
# Handles gaps, line breaks, and hyphenation.
def clean_text_from_words(words):
    if not words:
        return ""
    
    combined_text = ""
    prev_end_x = None
    prev_y = None

    # Calculate gaps between words
    gaps = [words[i][0] - words[i - 1][2] for i in range(1, len(words))] if len(words) > 1 else []
    median_gap = statistics.median(gaps) if gaps else 1.0  # Default median gap

    for word in words:
        x_start, x_end, y, text = word[0], word[2], word[1], word[4]
        
        if prev_end_x is not None:
            gap = x_start - prev_end_x

            if prev_y is not None and abs(y - prev_y) > 5:
                # If there's a significant y-coordinate difference, treat it as a new line
                combined_text += f" {text}"
            elif gap < 0.3 * median_gap:
                # Tight gap, merge without space
                combined_text += text
            else:
                # Moderate or large gap, add a space
                combined_text += f" {text}"

        else:
            combined_text += text  # First word

        prev_end_x = x_end  # Update end position
        prev_y = y

    # Post-process text to clean up spaces and handle hyphenated words
    combined_text = combined_text.replace("  ", " ").strip()

    # get rid of single letters
    combined_text = re.sub(r'\b[b-zB-Z]\b|\[\]', '', combined_text)

    # print(f"Post-processed text: {combined_text}")
    return combined_text
    


def extract_highlighted_text(doc_path, output_path):
    doc = fitz.open(doc_path)
    highlights = []

    with open(output_path, "w", encoding="utf-8") as output_file:
        for page_num in range(len(doc)):
            page = doc[page_num]

            for annot in page.annots():
                if annot.type[1] == "Highlight" and annot.vertices:
                    quad_points = annot.vertices

                    passage_text = []  # Temporary storage for text in the same passage
                    for i in range(0, len(quad_points), 4):
                        # Calculate rectangle with the 1st and 4th quadpoints
                        x0 = min(quad_points[i][0], quad_points[i + 3][0])
                        y0 = min(quad_points[i][1], quad_points[i + 3][1])
                        x1 = max(quad_points[i][0], quad_points[i + 3][0])
                        y1 = max(quad_points[i][1], quad_points[i + 3][1])
                        rect = fitz.Rect(x0, y0, x1, y1)

                        if rect.width > 0 and rect.height > 0:
                            words = page.get_text("words", clip=rect)
                            # print(f"Words in rectangle: {words}")           # debug
                            cleaned_text = clean_text_from_words(words)
                            # print(f"Cleaned text: {cleaned_text}")          # debug
                            if cleaned_text:
                                passage_text.append(cleaned_text)
                                #print(f"List of cleaned text: {passage_text}")

                    # Merge all lines for this set of quadpoints
                    if passage_text:
                        merged_text = " "
                        for i, line in enumerate(passage_text):
                            if i > 0 and merged_text.endswith("-"):
                                merged_text = merged_text[:-1] + line.lstrip()
                            else: 
                                # Append the current line with a space (if not the first line)
                                merged_text += ("" if i == 0 else " ") + line.strip()

                        merged_text = merged_text.strip()        

                        highlights.append({"page": page_num + 1, "text": merged_text})
                        output_file.write(f"{merged_text}\n")
                        # print(f"Merged text: {merged_text}\n")

    print(f"Extracted highlights saved to {output_path}")

# Example usage
pdf_path = r"C:\Users\Media\Documents\Forward College\readings\Term 4\Cognitive Psychology\Topic 7\Brosch et al._2013_topic 7.pdf" 
output_path = r"C:\Users\Media\Desktop\Python\output.txt"
extract_highlighted_text(pdf_path, output_path)