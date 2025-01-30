import java.util.Comparator;

import components.map.Map;
import components.map.Map.Pair;
import components.map.Map1L;
import components.queue.Queue;
import components.queue.Queue1L;
import components.set.Set;
import components.set.Set1L;
import components.simplereader.SimpleReader;
import components.simplereader.SimpleReader1L;
import components.simplewriter.SimpleWriter;
import components.simplewriter.SimpleWriter1L;

/**
 *
 * @author Hank Zhang
 */
public final class WordCounter {

    /**
     * No argument constructor--private to prevent instantiation.
     */
    private WordCounter() {
        // no code needed here
    }

    //from 2221 course
    /**
     * A comparator class that provides a case-insensitive comparison of
     * strings.
     * <p>
     * This comparator implements the {@code Comparator<String>} interface,
     * allowing it to compare two strings lexicographically, ignoring case
     * differences. It can be used to sort collections of strings in a
     * case-insensitive manner.
     * </p>
     *
     * <p>
     * <strong>Example Usage:</strong>
     * </p>
     * <pre>
     * List<String> strings = Arrays.asList("Apple", "banana", "Cherry");
     * Collections.sort(strings, new StringComparator());
     * System.out.println(strings); // Output: [Apple, banana, Cherry]
     * </pre>
     */
    private static final class StringComparator implements Comparator<String> {

        @Override
        public int compare(String str1, String str2) {
            return str1.compareToIgnoreCase(str2);
        }

    }

    /**
     * Defines the characters that are considered as word separators.
     *
     * @param separators
     *            The set to which separator characters will be added.
     */
    public static void defineWordSeparators(Set<Character> separators) {
        char[] separatorChars = { ' ', '.', ',', ':', ';', '?', '!', '"', '(', ')', '-',
                '\'' };
        for (char separator : separatorChars) {
            separators.add(separator);
        }
    }

    /**
     * Prints the HTML header for the output.
     *
     * @param output
     *            The output writer.
     */
    public static void printHTMLHeader(SimpleWriter output) {
        output.println("<!DOCTYPE html>");
        output.println("<html>\n\t<head>\n\t<style>\n"
                + "table, th, td{\nborder: 1px solid black;\n}th, td \n\t</style>");
        output.println("\n<title>" + "Words count" + "</title>\n\t</head>\n\t<body>\n"
                + "\t<h2><b>Words counted in: " + output.name() + "</b></h2>\n"
                + "<table style='width:50%'>\n"
                + "<tr><th>Words</th><th>Counts</th></tr>");
    }

    /**
     * Returns the first "word" (maximal length string of characters not in
     * {@code separators}) or "separator string" (maximal length string of
     * characters in {@code separators}) in the given {@code text} starting at
     * the given {@code position}.
     *
     * @param text
     *            the {@code String} from which to get the word or separator
     *            string
     * @param position
     *            the starting index
     * @param separators
     *            the {@code Set} of separator characters
     * @return the first word or separator string found in {@code text} starting
     *         at index {@code position}
     * @requires 0 <= position < |text|
     * @ensures <pre>
     * nextWordOrSeparator =
     *   text[position, position + |nextWordOrSeparator|)  and
     * if entries(text[position, position + 1)) intersection separators = {}
     * then
     *   entries(nextWordOrSeparator) intersection separators = {}  and
     *   (position + |nextWordOrSeparator| = |text|  or
     *    entries(text[position, position + |nextWordOrSeparator| + 1))
     *      intersection separators /= {})
     * else
     *   entries(nextWordOrSeparator) is subset of separators  and
     *   (position + |nextWordOrSeparator| = |text|  or
     *    entries(text[position, position + |nextWordOrSeparator| + 1))
     *      is not subset of separators)
     * </pre>
     */
    private static String nextWordOrSeparator(String text, int position,
            Set<Character> separators) {
        boolean isSeparator = separators.contains(text.charAt(position));
        String extracted = "" + text.charAt(position);
        boolean isNextCharSeparator;
        int index = 1;

        if (position + index < text.length()) {
            isNextCharSeparator = separators.contains(text.charAt(position + index));
        } else {
            isNextCharSeparator = !isSeparator;
        }

        while (isNextCharSeparator == isSeparator) {
            extracted += text.charAt(position + index);
            index++;

            if (position + index < text.length()) {
                isNextCharSeparator = separators.contains(text.charAt(position + index));
            } else {
                isNextCharSeparator = !isSeparator;
            }
        }
        return extracted;

    }

    /**
     * Prints the HTML footer for the output.
     *
     * @param output
     *            The output writer.
     */
    public static void printHTMLFooter(SimpleWriter output) {
        output.print("\t\t</table>\n" + "\t</body>\n" + "</html>");
    }

    /**
     * Generates an HTML page containing the word count results.
     *
     * @param countMap
     *            A map containing the word counts.
     * @param originalMap
     *            A map storing the original case of each word.
     * @param output
     *            The output writer.
     */
    private static void generateHTMLPage(Map<String, Integer> countMap,
            Map<String, String> originalMap, SimpleWriter output) {

        Comparator<String> alphabeticalOrder = new StringComparator();
        printHTMLHeader(output);
        Queue<String> allWords = new Queue1L<String>();

        for (Pair<String, Integer> pair : countMap) {

            allWords.enqueue(pair.key());
        }

        allWords.sort(alphabeticalOrder);

        for (String word : allWords) {

            output.print("\t\t\t<tr>\n\t\t\t\t<td>" + originalMap.value(word)
                    + "</td><td>" + countMap.value(word) + "</td>\n\t\t\t</tr>\n");
        }

        printHTMLFooter(output);
    }

    /**
     * Counts the words in the input and generates an HTML report.
     *
     * @param input
     *            The input reader.
     * @param output
     *            The output writer.
     */
    private static void countWords(SimpleReader input, SimpleWriter output) {
        String line;
        // it can be a separator as well.
        String word;

        int position;

        Set1L<Character> separators = new Set1L<Character>();
        defineWordSeparators(separators);

        Map1L<String, Integer> countMap = new Map1L<>();
        Map1L<String, String> originalMap = new Map1L<>();

        while (!input.atEOS()) {
            line = input.nextLine();
            position = 0;

            while (position < line.length()) {
                word = nextWordOrSeparator(line, position, separators);
                position = position + word.length();

                if (!separators.contains(word.charAt(0))) {
                    //we do care about cases. Keep both upper and lower case.
                    String lowerWord = word;

                    // Count words, maintaining original case for the first occurrence
                    if (countMap.hasKey(lowerWord)) {

                        countMap.replaceValue(lowerWord, countMap.value(lowerWord) + 1);

                    } else {
                        countMap.add(lowerWord, 1);

                        // Store the original case
                        originalMap.add(lowerWord, word);
                    }
                }
            }
        }

        generateHTMLPage(countMap, originalMap, output);
    }

    /**
     * Main method.
     *
     * @param args
     *            the command line arguments; unused here
     */
    public static void main(String[] args) {
        SimpleWriter out = new SimpleWriter1L();
        SimpleReader in = new SimpleReader1L();

        out.println("Please enter the file name you want to input: ");
        SimpleReader fileInput = new SimpleReader1L(in.nextLine());

        out.println("Please enter the file name you want to output: ");
        SimpleWriter fileOutput = new SimpleWriter1L(in.nextLine());
        countWords(fileInput, fileOutput);

        in.close();
        out.close();
    }

}
